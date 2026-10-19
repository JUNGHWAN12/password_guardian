import argparse
from datetime import datetime
from pathlib import Path
import sys
import traceback

from .rankings import RankingRepository, default_data_dir


def main():
    parser = argparse.ArgumentParser(description="패스워드 가디언 프로토타입")
    parser.add_argument("--windowed", action="store_true", help="창 모드로 시작(기본은 전체 화면)")
    parser.add_argument("--fullscreen", action="store_true", help="전체 화면으로 시작(기본값, 예전 실행 옵션 호환용)")
    parser.add_argument("--practice", action="store_true", help="랭킹에 저장하지 않는 연습 모드")
    parser.add_argument("--booth", action="store_true",
                        help="부스 런처용: 한 판이 끝나면 종료, 시작 화면 Esc·언제든 Shift+Esc로 종료")
    parser.add_argument("--data-dir", type=Path, default=default_data_dir(), help="랭킹 저장 폴더(기본: 게임 폴더의 data)")
    parser.add_argument("--backup", type=Path, help="랭킹 DB 백업 후 종료")
    parser.add_argument("--reset-rankings", action="store_true", help="백업 후 랭킹 초기화")
    parser.add_argument("--confirm-reset", action="store_true", help="초기화 명시적 확인")
    args = parser.parse_args()
    if args.reset_rankings and not (args.backup and args.confirm_reset):
        parser.error("초기화에는 --backup 새파일경로 --confirm-reset이 필요합니다.")
    if args.backup:
        repo = RankingRepository(args.data_dir / "ranking.json")
        print(f"랭킹 파일: {repo.path.resolve()}")
        if args.reset_rankings:
            repo.reset(args.backup)
            print("백업 검증 후 랭킹을 초기화했습니다.")
        else:
            repo.backup(args.backup)
            print(f"백업 완료: {args.backup.resolve()}")
        return
    try:
        import arcade
        from .app import GuardianWindow
        window = GuardianWindow(args.data_dir, fullscreen=not args.windowed, practice=args.practice, booth=args.booth)
        try:
            arcade.run()
        finally:
            if not window.closed_worker:
                window.worker.close()
    except Exception:
        # A windowed .exe has no console: keep the error in a file and exit non-zero for the launcher.
        log = args.data_dir / "error.log"
        try:
            log.parent.mkdir(parents=True, exist_ok=True)
            with log.open("a", encoding="utf-8") as f:
                f.write(f"--- {datetime.now().isoformat(timespec='seconds')}\n{traceback.format_exc()}")
        except OSError:
            pass
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
