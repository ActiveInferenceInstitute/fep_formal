"""One-timestep numerical checker; never a native or physical-model proof."""
import json
import math

FIELDS = {
    'model_name', 'framework', 'model_kind', 'num_timesteps', 'num_states',
    'num_observations', 'beliefs', 'posterior_cov', 'true_states_continuous',
    'observations_continuous', 'controls', 'control_mode', 'rmse_vs_true',
    'observations', 'actions', 'efe_history', 'validation',
    'execution_time_seconds', 'jax_version',
}
FLAGS = {'means_finite', 'posterior_cov_psd', 'rmse_finite', 'controls_finite', 'all_valid'}


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def strict_json(text):
    def nonfinite(value):
        raise ValueError('nonfinite JSON constant: ' + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=nonfinite)


def number(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('expected a finite real number, not a boolean')
    return float(value)


def close(actual, expected):
    if not math.isclose(number(actual), expected, rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError('independent scalar comparison failed')


def scalar_array(value, depth):
    for _ in range(depth):
        if type(value) is not list or len(value) != 1:
            raise ValueError('expected singleton scalar array dimensions')
        value = value[0]
    return number(value)


def validate(record, *, jax_version):
    if type(record) is not dict or set(record) != FIELDS:
        raise ValueError('unknown or missing output fields')
    expected = {
        'model_name': 'FepLean Continuous OU Linear-Gaussian Model',
        'framework': 'jax', 'model_kind': 'continuous',
        'control_mode': 'passive', 'jax_version': jax_version,
    }
    for key, value in expected.items():
        if record[key] != value:
            raise ValueError('unexpected output identity: ' + key)
    for key in ['num_timesteps', 'num_states', 'num_observations']:
        if type(record[key]) is not int or record[key] != 1:
            raise ValueError('unexpected declared dimensions')
    for key in ['observations', 'actions', 'efe_history']:
        if record[key] != []:
            raise ValueError('categorical output slots must remain empty')
    flags = record['validation']
    if type(flags) is not dict or set(flags) != FLAGS or any(v is not True for v in flags.values()):
        raise ValueError('declared validation is not complete and true')
    y = scalar_array(record['observations_continuous'], 2)
    x = scalar_array(record['true_states_continuous'], 2)
    mu = scalar_array(record['beliefs'], 2)
    covariance = scalar_array(record['posterior_cov'], 3)
    control = scalar_array(record['controls'], 2)
    close(mu, y / 2.0)
    close(covariance, 0.5)
    close(control, 0.0)
    close(record['rmse_vs_true'], abs(mu - x))
    if covariance <= 0 or number(record['execution_time_seconds']) < 0:
        raise ValueError('invalid covariance or elapsed time')
    return {
        'passed': True, 'observation': y, 'latent': x, 'posterior_mean': mu,
        'posterior_covariance': covariance, 'control': control,
        'boundary': 'Initial observation update only; F/Q prediction and OU dynamics were not exercised.',
    }


def validate_binding(observed, expected):
    if observed != expected:
        raise ValueError('missing, stale or replaced source/runtime binding')


def controls():
    import copy
    good = {
        'model_name': 'FepLean Continuous OU Linear-Gaussian Model',
        'framework': 'jax', 'model_kind': 'continuous', 'control_mode': 'passive',
        'jax_version': '0.9.2', 'num_timesteps': 1, 'num_states': 1,
        'num_observations': 1, 'beliefs': [[1.0]], 'posterior_cov': [[[0.5]]],
        'true_states_continuous': [[1.0]], 'observations_continuous': [[2.0]],
        'controls': [[0.0]], 'rmse_vs_true': 0.0, 'execution_time_seconds': 0.0,
        'observations': [], 'actions': [], 'efe_history': [],
        'validation': {key: True for key in FLAGS},
    }
    assert validate(good, jax_version='0.9.2')['passed']
    rejected = []
    for name, key, value in [
        ('missing', 'beliefs', None), ('malformed_shape', 'beliefs', [1.0]),
        ('wrong_covariance', 'posterior_cov', [[[0.6]]]),
        ('nonfinite', 'rmse_vs_true', float('nan')),
        ('boolean_dimension', 'num_timesteps', True),
        ('stale_tool', 'jax_version', '0.0.0'), ('extra', 'unknown', 'field'),
    ]:
        candidate = copy.deepcopy(good)
        if value is None:
            del candidate[key]
        else:
            candidate[key] = value
        try:
            validate(candidate, jax_version='0.9.2')
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError('accepted negative control: ' + name)
    for name, observed in [('missing_binding', {}), ('stale_binding', {'head': 'old'}), ('replacement_binding', {'head': 'other'})]:
        try:
            validate_binding(observed, {'head': 'frozen'})
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError('accepted negative binding: ' + name)
    for text in ['{"x": 1, "x": 2}', '{"x": NaN}', '{broken']:
        try:
            strict_json(text)
        except ValueError:
            rejected.append('strict_json')
        else:
            raise AssertionError('accepted malformed JSON')
    return {'positive_synthetic_fixture': True, 'rejected_controls': rejected, 'boundary': 'Synthetic checker controls only; no runner or empirical observations.'}


if __name__ == '__main__':
    print(json.dumps(controls(), indent=2))
