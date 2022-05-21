import numpy as np
from django.db.models import Count, F
from matplotlib import pyplot as plt
from tqdm import tqdm

from db.models import Transaction, Block


def reject_outliers(data, m=3):
    return data[abs(data - np.median(data)) < m * np.std(data)]


def draw():
    """
    Draw a boxplot of the fees compared to the block size
    :return:
    """
    print('Getting blocks')
    block_counts = Transaction.objects.values('block').annotate(size=Count('block_id'))
    sizes = [b['size'] for b in block_counts]
    print('Got blocks')

    print('Getting transactions')
    txs = Transaction.objects.values('block', 'weight').annotate(ratio=F('fee') * 1.0 / F('weight'))
    print('Got transactions', txs[0] and '')

    print('Collecting weights')
    weights = Block.objects.values('weight')
    weights = np.array([b['weight'] for b in weights])
    weights = reject_outliers(weights)

    tx_weights = np.array([t['weight'] for t in txs])
    tx_weights = reject_outliers(tx_weights)

    print('Computing service times')
    selection_times = Block.objects.values_list('time', flat=True).order_by('time')
    selection_times = np.array([t.timestamp() for t in selection_times])
    service_times = selection_times[1:] - selection_times[:-1]
    service_times = reject_outliers(service_times)

    print('Collecting fees')
    fnw_ratios = np.array([t['ratio'] for t in txs])
    fnw_ratios = reject_outliers(fnw_ratios)

    print('Classifying transactions by fees')
    bin_edges_congestion = np.histogram_bin_edges(sizes, bins='doane')
    bin_indices_congestion = np.digitize(sizes, bin_edges_congestion)

    block_id_to_bin_idx_congestion = {
        b['block']: bin_id - 1 for bin_id, b in zip(bin_indices_congestion, block_counts)
    }
    bins_congestion = [[] for _ in range(len(bin_edges_congestion))]
    for tx in tqdm(txs):
        bin_idx = block_id_to_bin_idx_congestion[tx['block']]
        bins_congestion[bin_idx].append(tx['ratio'])
    print('Classified transactions')

    print('Plot sizes')
    fig_sizes, ax_sizes = plt.subplots()
    title_sizes = "Histogramme des tailles des blocs"

    fig_sizes.canvas.manager.set_window_title(title_sizes)
    ax_sizes.set(title=title_sizes, xlabel='Nombre de transactions par bloc', ylabel='Nombre de blocs')

    ax_sizes.hist(sizes, bins='auto')

    print(f"{np.median(sizes)=}, {np.mean(sizes)=}")
    
    print('Plot weights')
    fig_weights, ax_weights = plt.subplots()
    title_weights = "Histogramme du poids des blocs"

    fig_weights.canvas.manager.set_window_title(title_weights)
    ax_weights.set(title=title_weights, xlabel='Poids des blocs (WU)', ylabel='Nombre de blocs')

    ax_weights.hist(weights, bins='auto')

    print(f"{np.median(weights)=}, {np.mean(weights)=}")
    
    print('Plot tx_weights')
    fig_tx_weights, ax_tx_weights = plt.subplots()
    title_tx_weights = "Histogramme du poids des transactions"

    fig_tx_weights.canvas.manager.set_window_title(title_tx_weights)
    ax_tx_weights.set(title=title_tx_weights, xlabel='Poids des transactions (WU)', ylabel='Nombre de transactions')

    ax_tx_weights.hist(tx_weights, bins='auto')

    print(f"{np.median(tx_weights)=}, {np.mean(tx_weights)=}")
    
    print('Plot service time')
    fig_service, ax_service = plt.subplots()
    title_service = "Histogramme du temps inter-bloc"

    fig_service.canvas.manager.set_window_title(title_service)
    ax_service.set(title=title_service, xlabel='Temps entre les blocs (secondes)', ylabel='Nombre de blocs')

    ax_service.hist(service_times, bins='auto')

    print(f"{np.median(service_times)=}, {np.mean(service_times)=}")
    
    print('Plot fee ratios')
    fig_fee_ratios, ax_fee_ratios = plt.subplots()
    title_fee_ratios = "Histogramme des ratios de récompense sur poids"

    fig_fee_ratios.canvas.manager.set_window_title(title_fee_ratios)
    ax_fee_ratios.set(title=title_fee_ratios, xlabel='Ratio des frais de transactions sur poids (satoshi/WU)', ylabel='Nombre de transactions')

    ax_fee_ratios.hist(fnw_ratios, bins='auto')

    print(f"{np.median(fnw_ratios)=}, {np.mean(fnw_ratios)=}")

    print('Plot Congestion')
    fig_congestion, ax_congestion = plt.subplots()
    title_congestion = "Ratio des frais sur poids des transactions en fonction de la taille de bloc"

    fig_congestion.canvas.manager.set_window_title(title_congestion)
    ax_congestion.set(title=title_congestion, xlabel='Nombre de transactions par bloc', ylabel='Ratio de frais sur poids (satoshi/WU)')

    labels_congestion = [f"{e:.0f}" for e in bin_edges_congestion]
    ax_congestion.boxplot(bins_congestion, labels=labels_congestion, showfliers=False, showmeans=True)
    ax_congestion.set_xticklabels(labels_congestion, rotation=45, ha='right')

    plt.show()
