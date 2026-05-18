import json
import os
import subprocess
import shutil
from datetime import datetime

from .weread_api import WeReadApi

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "OUT_FOLDER")


def sync_heatmap():
    print("正在生成阅读时间热力图...")

    weread = WeReadApi()
    read_times = _fetch_read_times(weread)
    if not read_times:
        print("  没有获取到阅读时间数据")
        return

    date_minutes = _convert_to_date_minutes(read_times)
    print(f"  获取到 {len(date_minutes)} 天的阅读数据")

    svg_path = _generate_heatmap_svg(date_minutes)
    if not svg_path:
        print("  热力图 SVG 生成失败")
        return

    os.makedirs(OUT_DIR, exist_ok=True)
    dest = os.path.join(OUT_DIR, "heatmap.svg")
    shutil.copy2(svg_path, dest)
    print(f"  热力图已生成: {dest}")


def _fetch_read_times(weread):
    """Fetch daily reading times using monthly mode for all available history."""
    all_read_times = {}
    current_year = datetime.now().year
    current_month = datetime.now().month

    # Try from 2020 onwards to cover all possible reading history
    for year in range(2020, current_year + 1):
        end_month = current_month if year == current_year else 12
        for month in range(1, end_month + 1):
            base_time = int(datetime(year, month, 15).timestamp())
            try:
                data = weread.get_read_detail(mode="monthly", base_time=base_time)
                read_times = data.get("readTimes") or {}
                if read_times:
                    all_read_times.update(read_times)
            except Exception:
                continue

    return all_read_times


def _convert_to_date_minutes(read_times):
    """Convert {timestamp_str: seconds} to {YYYY-MM-DD: minutes}."""
    result = {}
    for ts_str, seconds in read_times.items():
        try:
            ts = int(ts_str)
            date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            minutes = seconds // 60
            if minutes > 0:
                result[date_str] = minutes
        except (ValueError, OSError):
            continue
    return result


def _generate_heatmap_svg(date_minutes):
    """Write JSON and call github_heatmap CLI to generate SVG."""
    json_path = os.path.join(OUT_DIR, "data.json")
    os.makedirs(OUT_DIR, exist_ok=True)

    with open(json_path, "w") as f:
        json.dump(date_minutes, f)

    # Determine year range from actual data
    years = sorted(set(d[:4] for d in date_minutes.keys()))
    if years:
        year_arg = f"{years[0]}-{years[-1]}"
    else:
        year_arg = str(datetime.now().year)

    try:
        subprocess.run(
            [
                "github_heatmap", "json",
                "--json_file", json_path,
                "--year", year_arg,
                "--me", "WeRead",
                "--background-color", "#FFFFFF",
                "--track-color", "#ACE1AF",
                "--special-color1", "#69B578",
                "--special-color2", "#3A7D44",
                "--text-color", "#333333",
                "--dom-color", "#EBEDF0",
                "--unit", "min",
            ],
            cwd=OUT_DIR,
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"  github_heatmap 执行失败: {e.stderr.decode()}")
        return None
    except FileNotFoundError as e:
        print(f"  github_heatmap 执行失败: {e}")
        return None

    svg_path = os.path.join(OUT_DIR, "OUT_FOLDER", "json.svg")
    if os.path.exists(svg_path):
        return svg_path
    return None
