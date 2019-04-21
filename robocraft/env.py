from contextvars import Context, ContextVar


current_player = ContextVar("player")
game = ContextVar("game")
TICK = ContextVar("TICK")
