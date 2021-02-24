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
## SOLAR TESTS
# Test solar costing is correctly implemented
solar = {
    'solar_1_price_fluctuation': {
        'params': {
            # High initial price and high DHW demand (100% capacity) means constant heating but choice of source
            # Expect self-con, self-con, grid failover
            'I': [50, 5, 5, 5],
            'X': [20, 2, 2, 2],
            'G': [1.5, 1.5, 0, 0],
            'H': [0, 0, 0, 100]
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
    'solar_2_price_fluctuation': {
        'params': {
            # High initial price and moderate DHW demand (70% capacity) choice to export in one slot
            # Expect export, self-con, self-con w/ grid support
            'I': [50, 5, 5, 5],
            'X': [20, 2, 2, 2],
            'G': [0, 1.5, 0.5, 0],
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
            'cost': 5
        }
    },
}
## EXPORT TESTS
# Test exporting to grid is correctly implemented
export = {
    'export_1_price_crossover': {
        'params': {
            # Export price is higher than import price
            # System should not import to re-export
            # Expect nothing to happe
            'I': [0, 0, 0, 0],
            'X': [10, 10, 10, 10],
            'G': [0, 0, 0, 0],
            'H': [0, 0, 0, 0]
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
            'cost': 0
        }
    },
    'export_2_demandless_export': {
        'params': {
            # No demand, expect 100% exporting
            'I': [50, 5, 5, 5],
            'X': [5, 12, 7, 3],
            'G': [1, 1, 1, 1],
            'H': [0, 0, 0, 0]
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
            'cost': -27
        }
    },
}
## ADVANCED TESTS
# A bunch of interesting edge cases and difficult decisions
adv = {
    'adv_1_arbitrage': {
        'params': {
            # System has non-zero loss and expensive electricity outside of a window
            # Should self-consume and import during low export rate and a little bit afterwards
            # But export the bulk of the power
            # So usage ~0, 3, 1.5, N/A
            # Initial 10 and tiny loss mean only a little power is used at the start
            'I': [50, 5, 50, 0],
            'X': [30, 3, 30, 10],
            'G': [1.5, 1.5, 1.5, 0],
            'H': [0, 0, 0, 100]
        },
        'config': {
            'heater_power': 3,
            'litres_per_kWh': 20,
            'dilution': 1,
            'loss': 0.01,
            'w_init': 10,
            'tank_capacity': 100
        },
        'expectation': {
            'lp_status': 'Optimal',
            'cost': -36.12
        }
    },
    'adv_2_negative_export': {
        'params': {
            # It's a sunny day. No-one wants hot water, yet we've got all this solar
            #  to rid ourselves of. What should we do...?
            # System expected to export when forced to, but buy back to compensate loss
            # (Interestingly, the system imports 3kW in the last time slot even though there's no financial gain...
            #  As soon as there is financial gain, it stops :D )
            'I': [-3, -3, -3, -3],
            'X': [-5, -5, -5, -5],
            'G': [3, 4, 2, 0],
            'H': [0, 0, 0, 0]
        },
        'config': {
            'heater_power': 3,
            'litres_per_kWh': 20,
            'dilution': 1,
            'loss': 0,
            'w_init': 10,
            'tank_capacity': 1000
        },
        'expectation': {
            'lp_status': 'Optimal',
            'cost': -7
        }
    },
    'adv_3_full_24': {
        'params': {
            # It's a full 24hr period, with somewhat realistic pricing and demand. What happens....
            'I': [5, 5, 5, 5, 5, 5, 3, -5, -5, 0, 5, 5, 5, 7, 7, 10, 10, 10, 10, 10, 10, 10, 10, 7, 7, 7, 7, 7, 7, 7, 7, 7, 5, 30, 30, 30, 30, 30, 30, 30, 12, 12, 12, 7, 7, 7, 7, 7],
            'X': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 5, 5, 5, 5, 5, 5, 5, 5, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 25, 25, 25, 25, 25, 25, 25, 7, 7, 7, 2, 2, 2, 2, 2],
            'G': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.783134188, 1.552869522, 2.296036393, 2.999919759, 3.65247669, 4.242542412, 4.760021333, 5.196059767, 5.543197413, 5.795495002, 5.948635905, 5.999999994, 5.948708465, 5.795638881, 5.543410149, 5.19633772, 4.760359748, 4.242935499, 3.652917723, 3.000401193, 2.296549991, 1.553406496, 0.783685351, 0.000555922, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'H': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 10, 50, 50, 10, 10, 10, 10, 10, 10, 50, 50, 10, 10, 10, 10, 10, 10, 10, 100, 100, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        },
        'config': {
            'heater_power': 6,
            'litres_per_kWh': 20,
            'dilution': 1,
            'loss': 0.01,
            'w_init': 10,
            'tank_capacity': 450
        },
        'expectation': {
            'lp_status': 'Optimal',
            'cost': -7
        }
    },
}
