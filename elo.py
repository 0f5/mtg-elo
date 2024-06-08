mean_elo = 1500
elo_width = 400
k_factor = 64

def update_elo(elo1, elo2, result):
    """
    1 - player1 won
    0 - player2 won
    0.5 - draw
    """
    expected_win = expected_result(elo1, elo2)
    change_in_elo = k_factor * (result-expected_win)
    elo1 += change_in_elo
    elo2 -= change_in_elo
    return elo1, elo2

def expected_result(elo_a, elo_b):
    expect_a = 1.0/(1+10**((elo_b - elo_a)/elo_width))
    return expect_a
