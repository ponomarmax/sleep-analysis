import pandas as pd
from stream_buffer import StreamBuffer, normalize_ts_to_ns

def test_normalize_ts_to_ns_int_and_str():
    ts_int = 1_000_000_000
    assert normalize_ts_to_ns(ts_int) == ts_int

    ts_str = "2026-03-27 12:00:00"
    result = normalize_ts_to_ns(ts_str)
    assert isinstance(result, int)

    ts_pd = pd.Timestamp("2026-03-27 12:00:00")
    assert isinstance(normalize_ts_to_ns(ts_pd), int)

def test_streambuffer_append_and_trim():
    buf = StreamBuffer(max_seconds=1)  # 1 sec
    records = [{"ts": 1_000_000_000, "value": 1},
               {"ts": 2_000_000_000, "value": 2},
               {"ts": 3_500_000_000, "value": 3}]
    
    buf.append("stream1", records)
    df = buf.get_window("stream1", as_datetime=False)
    # Перевіряємо, що ts_ns додана
    assert all("ts_ns" in r for r in buf.buffers["stream1"])
    # Перевіряємо, що старі записи видалені (max_seconds=1)
    latest_ts = max(r["ts_ns"] for r in buf.buffers["stream1"])
    for r in buf.buffers["stream1"]:
        assert r["ts_ns"] >= latest_ts - buf.max_ns

def test_streambuffer_get_window_datetime_flag():
    buf = StreamBuffer()
    records = [{"ts": "2026-03-27 12:00:00", "value": 1}]
    buf.append("stream1", records)
    df_dt = buf.get_window("stream1", as_datetime=True)
    assert "ts" in df_dt.columns
    assert "ts_ns" in df_dt.columns

    df_no_dt = buf.get_window("stream1", as_datetime=False)
    assert "ts" in df_no_dt.columns
    assert "ts_ns" in df_no_dt.columns

def test_multiple_streams():
    buf = StreamBuffer()
    buf.append("s1", [{"ts": 1_000_000_000, "value": 1}])
    buf.append("s2", [{"ts": 1_500_000_000, "value": 2}])
    assert "s1" in buf.buffers and "s2" in buf.buffers