import numpy as np
from scipy.stats import kstest, expon
import statsmodels.api as sm

from db.models import Block


def test():
    selection_times = Block.objects.values_list('time', flat=True).order_by('time')
    selection_times = np.array([t.timestamp() for t in selection_times])
    service_times = selection_times[1:] - selection_times[:-1]

    from matplotlib import pyplot as plt
    fig, (ax_pdf, ax_qq) = plt.subplots(ncols=2)

    exp = expon(0, 1 * service_times.mean())
    x = np.linspace(exp.ppf(0.01), exp.ppf(0.99), 100)
    y = exp.pdf(x)

    ax_pdf.set(xlabel='Temps inter-bloc (secondes)', ylabel='Probabilité')
    ax_pdf.hist(service_times, label='Mesures', density=True, bins='auto')
    ax_pdf.plot(x, y, label=f"exp({1/service_times.mean():.3E})")
    ax_pdf.legend(loc='best', frameon=False)

    sm.qqplot(service_times, exp, line='45', ax=ax_qq)

    stat_test, p_value = kstest(service_times, exp.cdf, N=100, mode='exact', alternative='two-sided')
    print(f"Sample size : {len(service_times):,}")
    print(f"{stat_test = }, {p_value = }")

    plt.show()
