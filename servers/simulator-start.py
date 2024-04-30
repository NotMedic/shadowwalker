from collections import Counter
from itertools import product

DICE = {
    'Samurai': {'Attack': (1, 20), 'Damage': (3, 6), 'Heal': (1, 6)},
    'Decker':  {'Attack': (1, 20), 'Damage': (1, 6), 'Heal': (1, 6), 'Hack': (1, 20), 'HackDamage': (1, 8)},
    'Mage':    {'Attack': (1, 20), 'Damage': (1, 6), 'Heal': (1, 6), 'Magic': (4, 6), 'MagicDamage': (6, 6)},
    'Thug':    {'Attack': (1, 20), 'Damage': (1, 12), 'Heal': (1, 6)}
}

def multi_dice_probability(dice, sides):
    outcomes = [range(1, sides+1) for _ in range(dice)]
    sums = Counter()

    # Calculate all possible outcomes
    for outcome in product(*outcomes):
        sums[sum(outcome)] += 1

    total_outcomes = sides ** dice
    for outcome, count in sums.items():
        probability = (count / total_outcomes) * 100
        #print(f"The probability of rolling a {outcome} is {probability:.2f}%")

    # Calculate and print the mean
    mean = dice * (1 + sides) / 2
    print(f"The mean outcome is {mean}")

# Iterate through the character classes and report the mean for their Attack roll
for character_class, actions in DICE.items():
    dice, sides = actions['Attack']
    print(f"\n{character_class} Attack Roll:")
    multi_dice_probability(dice, sides)