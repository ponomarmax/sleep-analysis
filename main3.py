import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from bleak import BleakScanner
from polar_python import PolarDevice
from polar_python.models import HRData, ECGData, ACCData, PPGData, MAGData, GyroData, PPIData
import time
from recorder import Recorder
from serializers.json_serializer import JSONSerializer
from serializers.msgpack_serializer import MsgpackSerializer


serializers = {
    "ppg": MsgpackSerializer(),
    "acc": MsgpackSerializer(),
    "hr": MsgpackSerializer(),
    "mag": MsgpackSerializer(),
    "gyro": MsgpackSerializer(),
    "ppi": MsgpackSerializer(),
}

recorder = Recorder(serializers)

# -----------------------
# CONFIG
# -----------------------
DEVICE_NAME = "Polar Sense B15"
OUTPUT_DIR = Path("polar_data")
RECONNECT_DELAY = 5  # seconds

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def callback_factory(stream_name: str, filename: Path) -> Callable:

    def callback(data):
        recorder.write(
                stream=stream_name,
                # if data has timestamp attribute, use it, otherwise use current time utc timestamp The method "utcnow" in class "datetime" is deprecated
                ts=getattr(data, "timestamp", datetime.utcnow()),
                data=data
            )

    return callback

# -----------------------
# DEVICE HANDLER
# -----------------------
class PolarHandler:
    def __init__(self, device_name: str):
        self.device_name = device_name
        self.device: PolarDevice | None = None
        self.stream_files = {
            "ppg": OUTPUT_DIR / "ppg.jsonl",
            "hr": OUTPUT_DIR / "hr.jsonl",
            "ecg": OUTPUT_DIR / "ecg.jsonl",
            "acc": OUTPUT_DIR / "acc.jsonl",
            "mag": OUTPUT_DIR / "mag.jsonl",
            "gyro": OUTPUT_DIR / "gyro.jsonl",
            "ppi": OUTPUT_DIR / "ppi.jsonl",
        }

    async def connect(self):
        logging.info(f"Scanning for {self.device_name}...")
        device = await BleakScanner.find_device_by_filter(
            lambda bd, ad: bd.name and self.device_name in bd.name,
            timeout=10
        )
        if not device:
            raise RuntimeError(f"{self.device_name} not found nearby.")
        logging.info(f"Found {device.name}, connecting...")
        self.device = PolarDevice(device)
        await self.device.connect()
        logging.info("Connected.")

    async def start_streams(self):
        if not self.device:
            raise RuntimeError("Device not connected.")

        # HR
        await self.device.start_hr_stream(hr_callback=callback_factory("hr", self.stream_files["hr"]))

        # PPG
        await self.device.start_ppg_stream(
            ppg_callback=callback_factory("ppg", self.stream_files["ppg"]),
            sample_rate=55,
            resolution=22,
            channels=4
        )

        # # ACC
        await self.device.start_acc_stream(
            acc_callback=callback_factory("acc", self.stream_files["acc"]),
            sample_rate=52,
            resolution=16,
            range=8,
            channels=3
        )
        # # PPI
        await self.device.start_ppi_stream(ppi_callback=callback_factory("ppi", self.stream_files["ppi"]))


        # Gyroscope
        await self.device.start_gyro_stream(
            gyro_callback=callback_factory("gyro", self.stream_files["gyro"]),
            sample_rate=52,
            resolution=16,
            range=2000,
            channels=3
        )

        # # Magnetometer (MAG)
        await self.device.start_mag_stream(
            mag_callback=callback_factory("mag", self.stream_files["mag"]),
            sample_rate=50,
            resolution=16,
            range=50,
            channels=3
        )

    async def stop_streams(self):
        if self.device:
            await self.device.stop_hr_stream()
            await self.device.stop_ppg_stream()
            await self.device.stop_ppi_stream()
            await self.device.stop_acc_stream()
            await self.device.stop_gyro_stream()
            await self.device.stop_mag_stream()

    async def disconnect(self):
        if self.device:
            await self.device.disconnect()
            self.device = None
            logging.info("Disconnected.")

    async def run(self):
        while True:
            try:
                await self.connect()
                await self.start_streams()
                # просто спимо поки все працює, будь-яка помилка зламає цикл і виконається reconnect
                while True:
                    await asyncio.sleep(1)
            except Exception as e:
                logging.error(f"Error in device loop: {e}", exc_info=True)
            finally:
                await self.stop_streams()
                await self.disconnect()
                logging.info(f"Reconnecting in {RECONNECT_DELAY} seconds...")
                await asyncio.sleep(RECONNECT_DELAY)

# -----------------------
# MAIN
# -----------------------
async def main():
    handler = PolarHandler(DEVICE_NAME)
    await handler.run()

if __name__ == "__main__":
    asyncio.run(main())