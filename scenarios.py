# BASIC SCENARIOS
# Anything should pass this
basic = {
    'basic_1_future_demand': {
        'params': {
            'I': [5, 5, 5, 5],
            'X': [0, 0, 0, 0],
            'G': [0, 0, 0, 0],
            'H': [0, 0, 0, 70]
        },
        'config': {
            'heater_power': 1.5,
            'litres_per_kWh': 20,
            'dilution': 1,
            'loss': 0,
            'w_init': 10,
            'tank_capacity': 100
        },
        'expectation': {
            'lp_status': 'Optimal',
            'cost': 15
        }
    },
    # Cost Optimisation Test
    # System should only use the low price energy
    'basic_2_low_cost': {
        'params': {
            'I': [5, 50, 50, 50],
            'X': [0, 0, 0, 0],
            'G': [0, 0, 0, 0],
            'H': [0, 0, 0, 40]
        },
        'config': {
            'heater_power': 1.5,
            'litres_per_kWh': 20,
            'dilution': 1,
            'loss': 0,
            'w_init': 10,
            'tank_capacity': 100
        },
        'expectation': {
            'lp_status': 'Optimal',
            'cost': 7.5
        }
    },
    # 'Necessary Evil' case
    # System should use all the cheap energy it can, but that won't be enough
    'basic_3_necessary_evil': {
        'params': {
            'I': [5, 50, 50, 50],
            'X': [0, 0, 0, 0],
            'G': [0, 0, 0, 0],
            'H': [0, 0, 0, 70]
        },
        'config': {
            'heater_power': 1.5,
            'litres_per_kWh': 20,
            'dilution': 1,
            'loss': 0,
            'w_init': 10,
            'tank_capacity': 100
        },
        'expectation': {
            'lp_status': 'Optimal',
            'cost': 82.5
        }
    },
}

# LOSS SCENARIOS
# Requires implementation of loss
loss = {
    # Lost-value test
    # Enough heat is lost that more expensive electricity is viable
    'loss_1_lost_value': {
        'params': {
            'I': [5, 5, 10, 10],
            'X': [0, 0, 0, 0],
            'G': [0, 0, 0, 0],
            'H': [0, 0, 0, 30]
        },
        'config': {
            'heater_power': 1.5,
            'litres_per_kWh': 20,
            'dilution': 1,
            'loss': 0.6,
            'w_init': 0,
            'tank_capacity': 100
        },
        'expectation': {
            'lp_status': 'Optimal',
            'cost': 15
        }
    },
    # Lost-value test
    # Enough heat is lost that more expensive electricity is somewhat viable
    # But the slight decrease in loss means heating early is cheaper
    'loss_2_lost_value': {
        'params': {
            'I': [5, 5, 10, 10],
            'X': [0, 0, 0, 0],
            'G': [0, 0, 0, 0],
            'H': [0, 0, 0, 30]
        },
        'config': {
            'heater_power': 1.5,
            'litres_per_kWh': 20,
            'dilution': 1,
            'loss': 0.49,
            'w_init': 0,
            'tank_capacity': 100
        },
        'expectation': {
            'lp_status': 'Optimal',
            'cost': 14.85
        }
    },
}
