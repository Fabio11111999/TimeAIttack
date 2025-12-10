import viewer
import game
import make_replay


def main():

    game1 = game.Game(1920, 1080, "../tracks/drawer/")
    replay = game1.new_game()
    replay.print_to_file("refactor.txt")
    return
    """
    viewer1 = viewer.Viewer(1920, 1080, '../tracks/track1/')
    replay = make_replay.replay()
    replay.read_from_file('13.82.txt')
    viewer1.view(replay)
    """


if __name__ == "__main__":
    main()
