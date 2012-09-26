#!/usr/bin/env python
import pygame, sys, argparse, logging, time
from async import AsyncJsonTcp

black = 0, 0, 0
white = 255, 255, 255

class Paddle(object):
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

class Ball(object):
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius

class Level(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height

class GameInfo(object):
    def __init__(self, data):
        self.time = data['time']
        self.tick = data['conf']['tickInterval']
        self.level = Level(
            data['conf']['maxWidth'],
            data['conf']['maxHeight'],
        )
        self.left = Paddle(
            0,
            data['left']['y'],
            data['conf']['paddleWidth'],
            data['conf']['paddleHeight'],
        )
        self.right = Paddle(
            data['conf']['maxWidth'] - data['conf']['paddleWidth'],
            data['right']['y'],
            data['conf']['paddleWidth'],
            data['conf']['paddleHeight'],
        )
        self.ball = Ball(
            data['ball']['pos']['x'],
            data['ball']['pos']['y'],
            data['conf']['ballRadius'],
        )

class PongState(object):
    def __init__(self, conn, log):
        self.conn = conn
        self.log = log
        self.motor = 0.0
        self.game = None
        self.lastMessage = time.time()
        self.lastValue = 0.0
    
    def request_game(self, teamname, duelname=None):
        if duelname:
            self.conn.send({'msgType': 'requestDuel', 'data':[teamname, duelname]})
        else:
            self.conn.send({'msgType': 'join', 'data': teamname})

    def update(self):
        rsp_handlers = {
            'joined': self.on_game_joined,
            'gameStarted': self.on_game_started,
            'gameIsOn': self.on_game_is_on,
            'gameIsOver': self.on_game_over
        }
        for rsp in self.conn.receive(8):
            msg_type, data = rsp['msgType'], rsp['data']
            if msg_type in rsp_handlers:
                rsp_handlers[msg_type](data)

    def on_game_joined(self, data):
        self.log.info('Game visualization url: %s' % data)

    def on_game_started(self, data):
        self.log.info('Game started: %s vs. %s' % (data[0], data[1]))

    def on_game_is_on(self, data):
        self.game = GameInfo(data)
        now = time.time()
        if now > self.lastMessage + 0.1:
            if self.lastValue != self.motor:
                self.conn.send({'msgType': 'changeDir', 'data': self.motor})
                self.lastValue = self.motor
                self.lastMessage = now


    def on_game_over(self, data):
        self.log.info('Game ended. Winner: %s' % data)
        self.game = None

def paddle_frame(screen, paddle):
    area = paddle.x, paddle.y, paddle.width, paddle.height
    screen.fill(white, area)

def ball_frame(screen, ball):
    area = ball.x, ball.y, 2*ball.radius, 2*ball.radius
    screen.fill(white, area)

def level_frame(screen, level):
    area = 0, 0, level.width, 2
    screen.fill(white, area)
    area = 0, level.height - 2, level.width, 2
    screen.fill(white, area)

def animation_frame(screen):
    game = pong.game
    if game == None:
        return
    screen.fill(black)
    level_frame(screen, game.level)
    ball_frame(screen, game.ball)
    paddle_frame(screen, game.left)
    paddle_frame(screen, game.right)

def keydown(key):
    if key == pygame.K_ESCAPE:
        sys.exit(0)
    if key == pygame.K_DOWN:
        pong.motor = +1.0
    if key == pygame.K_UP:
        pong.motor = -1.0

def keyup(key):
    if key == pygame.K_DOWN or key == pygame.K_UP:
        pong.motor = 0.0

def dispatch(event):
    if event.type == pygame.QUIT:
        sys.exit(0)
    if event.type == pygame.KEYDOWN:
        keydown(event.key)
    if event.type == pygame.KEYUP:
        keyup(event.key)

def main():
    pygame.display.init()
    screen = pygame.display.set_mode((1024, 768))
    while 1:
        for event in pygame.event.get():
            dispatch(event)
        animation_frame(screen)
        pygame.display.flip()
        pong.update()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="play against a helloworldopen bot")
    parser.add_argument('-d', dest="duelname")
    parser.add_argument('teamname')
    parser.add_argument('hostname')
    parser.add_argument('port')
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                        level=logging.INFO)
    log = logging.getLogger(__name__)

    conn = AsyncJsonTcp(args.hostname, args.port)

    pong = PongState(conn, log)
    pong.request_game(args.teamname, args.duelname)

    main()
