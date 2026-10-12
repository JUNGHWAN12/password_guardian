import argparse
from pathlib import Path

from .rankings import RankingRepository, default_data_dir


def main():
    parser = argparse.ArgumentParser(description="패스워드 가디언 프로토타입")
    parser.add_argument("--fullscreen", action="store_true", help="전체 화면으로 시작")
    parser.add_argument("--practice", action="store_true", help="랭킹에 저장하지 않는 연습 모드")
    parser.add_argument("--data-dir", type=Path, default=default_data_dir(), help="랭킹 저장 폴더")
    parser.add_argument("--backup", type=Path, help="랭킹 DB 백업 후 종료")
    parser.add_argument("--reset-rankings", action="store_true", help="백업 후 랭킹 초기화")
    parser.add_argument("--confirm-reset", action="store_true", help="초기화 명시적 확인")
    args = parser.parse_args()
    if args.reset_rankings and not (args.backup and args.confirm_reset):
        parser.error("초기화에는 --backup 새파일경로 --confirm-reset이 필요합니다.")
    if args.backup:
        repo = RankingRepository(args.data_dir / "rankings.sqlite3")
        print(f"DB: {repo.path.resolve()}")
        if args.reset_rankings:
            repo.reset(args.backup)
            print("백업 검증 후 랭킹을 초기화했습니다.")
        else:
            repo.backup(args.backup)
            print(f"백업 완료: {args.backup.resolve()}")
        return
    import arcade
    from .app import GuardianWindow
    window = GuardianWindow(args.data_dir, fullscreen=args.fullscreen, practice=args.practice)
    try:
        arcade.run()
    finally:
        if not window.closed_worker:
            window.worker.close()


if __name__ == "__main__":
    main()
