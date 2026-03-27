from collections import deque
import pandas as pd

NS_IN_SECOND = 1_000_000_000


def normalize_ts_to_ns(ts):
    """
    Convert timestamp to int64 nanoseconds.
    """
    if isinstance(ts, int):
        return ts

    # fallback for string / datetime
    return int(pd.to_datetime(ts).value)


class StreamBuffer:
    def __init__(self, max_seconds=10):
        self.buffers = {}
        self.max_seconds = max_seconds
        self.max_ns = max_seconds * NS_IN_SECOND

    def append(self, stream, records):
        if stream not in self.buffers:
            self.buffers[stream] = deque()

        buf = self.buffers[stream]

        for r in records:
            # 🔴 normalize ONCE
            ts_ns = normalize_ts_to_ns(r["ts"])
            r["ts_ns"] = ts_ns

            buf.append(r)

        self._trim(stream)

    def _trim(self, stream):
        buf = self.buffers[stream]
        if not buf:
            return

        latest_ts = buf[-1]["ts_ns"]
        cutoff = latest_ts - self.max_ns

        # 🔥 fast loop without pandas
        while buf and buf[0]["ts_ns"] < cutoff:
            removed = buf.popleft()

    def get_window(self, stream, as_datetime=True):
        if stream not in self.buffers:
            return pd.DataFrame()

        df = pd.DataFrame(self.buffers[stream])

        if df.empty:
            return df

        # ✔ canonical column always exists
        if as_datetime:
            df["ts"] = pd.to_datetime(df["ts_ns"])

        return df