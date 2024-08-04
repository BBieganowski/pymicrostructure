"""Tools for creating ensembles of traders."""


def ensemble_traders(trader, params_dict):
    """Create an ensemble of traders with different parameter sets.

    Parameters:
    -----------
    trader : class
        The trader class to instantiate.
    params_dict : dict
        A dictionary of parameter names and lists of values.

    Returns:
    --------
    instances : list
        A list of trader instances.
    """
    instances = []
    for param_set in zip(*params_dict.values()):
        instance = trader(**dict(zip(params_dict.keys(), param_set)))
        instance.include_in_results = False
        instances.append(instance)
    return instances
