import sys
import cli, engine

def main():
    config = cli.parse_args(sys.argv[1:])
    game_engine = engine.Engine(config)
    game_engine.loop()

if __name__ == '__main__':
    main()