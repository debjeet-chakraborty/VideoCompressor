from __future__ import annotations

import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from dataclasses import asdict, dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


HOST = "127.0.0.1"
PORT = int(os.environ.get("VIDEO_COMPRESSOR_PORT", "8765"))
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)).resolve()
TASKS: dict[str, "CompressionTask"] = {}
TASK_LOCK = threading.Lock()
ENCODER_SUPPORT: dict[str, bool] = {}


@dataclass
class CompressionTask:
    id: str
    input_path: str
    output_path: str
    status: str = "queued"
    progress: float = 0.0
    stage: str = "Waiting"
    message: str = ""
    error: str = ""
    original_size: int = 0
    output_size: int = 0
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    cancel_requested: bool = False

    def public(self) -> dict[str, Any]:
        data = asdict(self)
        data["input_name"] = Path(self.input_path).name
        data["output_name"] = Path(self.output_path).name
        data["original_size_label"] = format_bytes(self.original_size)
        data["output_size_label"] = format_bytes(self.output_size)
        data["reduction"] = (
            round((1 - self.output_size / self.original_size) * 100, 1)
            if self.original_size and self.output_size
            else None
        )
        return data


def format_bytes(value: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{value} B"


def exe_name(name: str) -> str:
    return f"{name}.exe" if os.name == "nt" else name


def find_tool(name: str) -> str:
    local = ROOT / "bin" / exe_name(name)
    if local.exists():
        return str(local)
    system = shutil.which(name)
    if system:
        return system
    raise RuntimeError(
        f"{name} was not found. Install ffmpeg or place {exe_name(name)} in the app's bin folder."
    )


def dialog_open_file() -> str | None:
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        filename = filedialog.askopenfilename(
            title="Choose a video file",
            filetypes=[
                ("Video files", "*.mp4 *.mov *.mkv *.avi *.webm *.m4v *.flv *.wmv"),
                ("All files", "*.*"),
            ],
        )
        root.destroy()
        return filename or None
    except Exception:
        return None


def dialog_save_file(default_name: str) -> str | None:
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        filename = filedialog.asksaveasfilename(
            title="Save compressed video as",
            defaultextension=".mp4",
            initialfile=default_name,
            filetypes=[("MP4 video", "*.mp4"), ("All files", "*.*")],
        )
        root.destroy()
        return filename or None
    except Exception:
        return None


def video_info(input_path: str) -> tuple[float, bool]:
    result = subprocess.run(
        [
            find_tool("ffmpeg"),
            "-hide_banner",
            "-i",
            input_path,
        ],
        text=True,
        capture_output=True,
    )
    output = f"{result.stdout}\n{result.stderr}"
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", output)
    duration = 0.0
    if match:
        hours, minutes, seconds = match.groups()
        duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    has_audio = "Audio:" in output
    return duration, has_audio


def supports_encoder(encoder: str) -> bool:
    if encoder in ENCODER_SUPPORT:
        return ENCODER_SUPPORT[encoder]
    try:
        result = subprocess.run(
            [find_tool("ffmpeg"), "-hide_banner", "-encoders"],
            text=True,
            capture_output=True,
            check=False,
        )
        ENCODER_SUPPORT[encoder] = encoder in f"{result.stdout}\n{result.stderr}"
    except Exception:
        ENCODER_SUPPORT[encoder] = False
    return ENCODER_SUPPORT[encoder]


def parse_progress(line: str, duration: float) -> float | None:
    if not duration:
        return None
    match = re.search(r"out_time_ms=(\d+)", line)
    if match:
        return min(99.0, int(match.group(1)) / 1_000_000 / duration * 100)
    match = re.search(r"out_time=([0-9:.]+)", line)
    if not match:
        return None
    parts = match.group(1).split(":")
    seconds = float(parts[-1]) + int(parts[-2]) * 60 + int(parts[-3]) * 3600
    return min(99.0, seconds / duration * 100)


def build_ffmpeg_command(
    input_path: str,
    output_path: str,
    duration: float,
    has_audio: bool,
    target_reduction: float,
    quality_mode: str,
) -> list[str]:
    original_size = os.path.getsize(input_path)
    target_size = max(1, int(original_size * (1 - target_reduction / 100)))
    audio_bitrate = 128_000 if has_audio else 0
    target_total_bitrate = int((target_size * 8) / max(duration, 1))
    video_bitrate = max(250_000, target_total_bitrate - audio_bitrate)

    crf_by_mode = {"quality": "24", "balanced": "27", "smallest": "30"}
    preset_by_mode = {"quality": "slow", "balanced": "medium", "smallest": "slow"}

    video_encoder = "libx265" if supports_encoder("libx265") else "libx264"
    command = [find_tool("ffmpeg"), "-hide_banner", "-y", "-i", input_path, "-map", "0:v:0"]
    if has_audio:
        command += ["-map", "0:a?"]
    command += [
        "-c:v",
        video_encoder,
        "-preset",
        preset_by_mode.get(quality_mode, "medium"),
        "-crf",
        crf_by_mode.get(quality_mode, "27"),
        "-maxrate",
        str(video_bitrate),
        "-bufsize",
        str(video_bitrate * 2),
    ]
    if video_encoder == "libx265":
        command += ["-tag:v", "hvc1"]
    if has_audio:
        command += ["-c:a", "aac", "-b:a", "128k"]
    command += ["-movflags", "+faststart", "-progress", "pipe:1", "-nostats", output_path]
    return command


def compress_worker(task_id: str, target_reduction: float, quality_mode: str) -> None:
    with TASK_LOCK:
        task = TASKS[task_id]
        task.status = "running"
        task.stage = "Reading video metadata"
        task.original_size = os.path.getsize(task.input_path)

    process: subprocess.Popen[str] | None = None
    try:
        duration, has_audio = video_info(task.input_path)
        command = build_ffmpeg_command(
            task.input_path, task.output_path, duration, has_audio, target_reduction, quality_mode
        )
        with TASK_LOCK:
            task.stage = "Compressing"
            task.message = "Encoding with H.265. Large files can take a while."

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        assert process.stdout is not None
        for line in process.stdout:
            with TASK_LOCK:
                if task.cancel_requested and process.poll() is None:
                    process.terminate()
                    task.status = "cancelled"
                    task.stage = "Cancelled"
                    break
            progress = parse_progress(line.strip(), duration)
            if progress is not None:
                with TASK_LOCK:
                    task.progress = progress

        stderr = process.stderr.read() if process.stderr else ""
        return_code = process.wait()
        with TASK_LOCK:
            if task.status == "cancelled":
                task.finished_at = time.time()
                return
            if return_code != 0:
                task.status = "error"
                task.stage = "Failed"
                task.error = stderr[-4000:] or f"ffmpeg exited with code {return_code}"
                task.finished_at = time.time()
                return
            task.output_size = os.path.getsize(task.output_path)
            task.progress = 100.0
            task.status = "done"
            task.stage = "Complete"
            task.finished_at = time.time()
            task.message = (
                "Finished with at least 75% size reduction."
                if task.original_size and task.output_size <= task.original_size * 0.25
                else "Finished. This source could not reach a 75% reduction with the selected quality settings."
            )
    except Exception as exc:
        if process and process.poll() is None:
            process.kill()
        with TASK_LOCK:
            task.status = "error"
            task.stage = "Failed"
            task.error = str(exc)
            task.finished_at = time.time()


def json_response(handler: BaseHTTPRequestHandler, payload: dict[str, Any], status: int = 200) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length") or 0)
    if not length:
        return {}
    return json.loads(handler.rfile.read(length).decode("utf-8"))


class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_HEAD(self) -> None:
        parsed = urlparse(self.path)
        file_path = ROOT / "templates" / "index.html" if parsed.path == "/" else ROOT / unquote(parsed.path.lstrip("/"))
        resolved = file_path.resolve()
        if not str(resolved).startswith(str(ROOT)) or not resolved.is_file():
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(str(resolved))[0] or "application/octet-stream")
        self.send_header("Content-Length", str(resolved.stat().st_size))
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/":
            self.serve_file(ROOT / "templates" / "index.html")
            return
        if path.startswith("/static/"):
            self.serve_file(ROOT / unquote(path.lstrip("/")))
            return
        if path.startswith("/api/progress/"):
            task_id = path.rsplit("/", 1)[-1]
            with TASK_LOCK:
                task = TASKS.get(task_id)
                if not task:
                    json_response(self, {"error": "Task not found."}, HTTPStatus.NOT_FOUND)
                    return
                json_response(self, task.public())
            return
        json_response(self, {"error": "Not found."}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            if path == "/api/choose-input":
                json_response(self, {"path": dialog_open_file()})
                return
            if path == "/api/choose-output":
                body = read_json(self)
                input_path = body.get("input_path", "")
                default = f"{Path(input_path).stem or 'compressed'}-compressed.mp4"
                json_response(self, {"path": dialog_save_file(default)})
                return
            if path == "/api/start":
                self.start_task()
                return
            if path.startswith("/api/cancel/"):
                task_id = path.rsplit("/", 1)[-1]
                with TASK_LOCK:
                    task = TASKS.get(task_id)
                    if not task:
                        json_response(self, {"error": "Task not found."}, HTTPStatus.NOT_FOUND)
                        return
                    task.cancel_requested = True
                    json_response(self, task.public())
                return
            json_response(self, {"error": "Not found."}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            json_response(self, {"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def start_task(self) -> None:
        body = read_json(self)
        input_path = str(body.get("input_path", "")).strip()
        output_path = str(body.get("output_path", "")).strip()
        quality_mode = str(body.get("quality_mode", "balanced"))
        target_reduction = float(body.get("target_reduction", 75))

        if not input_path or not Path(input_path).is_file():
            json_response(self, {"error": "Choose a valid local video file."}, HTTPStatus.BAD_REQUEST)
            return
        if not output_path:
            json_response(
                self,
                {"error": "Choose where to save the compressed video."},
                HTTPStatus.BAD_REQUEST,
            )
            return
        if Path(input_path).resolve() == Path(output_path).resolve():
            json_response(
                self,
                {"error": "Output file must be different from the input file."},
                HTTPStatus.BAD_REQUEST,
            )
            return

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        task_id = uuid.uuid4().hex
        task = CompressionTask(task_id, input_path, output_path)
        with TASK_LOCK:
            TASKS[task_id] = task
        thread = threading.Thread(
            target=compress_worker,
            args=(task_id, target_reduction, quality_mode),
            daemon=True,
        )
        thread.start()
        json_response(self, task.public())

    def serve_file(self, file_path: Path) -> None:
        resolved = file_path.resolve()
        if not str(resolved).startswith(str(ROOT)) or not resolved.is_file():
            json_response(self, {"error": "Not found."}, HTTPStatus.NOT_FOUND)
            return
        body = resolved.read_bytes()
        content_type = mimetypes.guess_type(str(resolved))[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def open_browser() -> None:
    time.sleep(0.8)
    webbrowser.open(f"http://{HOST}:{PORT}")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), RequestHandler)
    threading.Thread(target=open_browser, daemon=True).start()
    print(f"Offline Video Compressor running at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
