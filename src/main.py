import viewer
import game
import make_replay


def main():
    game1 = game.game(1920, 1080, '../tracks/track1/')
    replay = game1.new_game()
    return
    replay.print_to_file('replay_nuovo.txt')
    viewer1 = viewer.viewer(1920, 1080, '../tracks/track1/')
    replay = make_replay.replay()
    replay.read_from_file('replay_nuovo.txt')
    viewer1.view(replay)


if __name__ == '__main__':
    main()
