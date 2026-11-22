"""Small reproducible simulation and classroom plots; fitting stays visible in notebooks."""
from pathlib import Path
import numpy as np
import pandas as pd
import anndata as ad
import mudata as md
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scipy.linalg import subspace_angles

PROCESSES = ['Inflammation', 'Metabolism', 'RNA program', 'Protein program', 'Planet response', 'Technical']
SPEC = dict(seed=2026, samples={'Asteron': 80, 'Borealis': 72},
            features={'RNA': 90, 'Protein': 60}, diseased={'Asteron': 40, 'Borealis': 48},
            noise_sd={'RNA': .55, 'Protein': 1.1}, n_processes=6)
COLORS = {'RNA': '#377eb8', 'Protein': '#e78b32', 'Asteron': '#548a64', 'Borealis': '#9865a8'}
DISEASE_COLORS = {'Healthy': '#1f77b4', 'Diseased': '#ff7f0e'}
ROOT = Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.size': 12, 'figure.figsize': (8, 4), 'axes.spines.top': False,
                     'axes.spines.right': False, 'figure.dpi': 110})

def simulate():
    """One frozen sample-level experiment. Truth never enters AnnData."""
    rng = np.random.default_rng(SPEC['seed'])
    weights = {}
    for view, d in SPEC['features'].items():
        w = np.zeros((6, d))
        w[0, :14] = rng.uniform(.8, 1.3, 14)
        w[1, 14:30] = rng.uniform(.8, 1.3, 16)
        w[2 if view == 'RNA' else 3, 30:44] = rng.uniform(.9, 1.4, 14)
        w[4, 44:56] = rng.uniform(.8, 1.3, 12)
        w[5] = rng.normal(0, .50 if view == 'RNA' else .15, d)
        weights[view] = w
    data, teacher = {}, {'scores': {}, 'weights': weights, 'contributions': {},
                         'noise': {}, 'intercepts': {}}
    for group, n in SPEC['samples'].items():
        ids = pd.Index([f'{group}_{i:03d}' for i in range(n)])
        disease = np.arange(n) < SPEC['diseased'][group]
        rng.shuffle(disease)
        batch = rng.integers(0, 2, n)
        z = rng.normal(size=(n, 6))
        z[:, 0] = .55*z[:, 0] + (disease.astype(float)-.5)*1.6
        z[:, 1] *= 2.0  # strong, disease-independent metabolic variability
        z[:, 4] *= .15 if group == 'Asteron' else 1.6
        z[:, 5] = (batch-.5)*3 + rng.normal(0, .3, n)
        obs = pd.DataFrame({'planet': group, 'disease': np.where(disease, 'Diseased', 'Healthy'),
                            'batch': batch.astype(str)}, index=ids)
        data[group] = {}
        teacher['scores'][group] = pd.DataFrame(z, index=ids, columns=PROCESSES)
        for key in ['contributions', 'noise', 'intercepts']: teacher[key][group] = {}
        for view, w in weights.items():
            mu = (np.arange(w.shape[1]) < 10) * (1.8 if group == 'Borealis' else 0)
            parts = z[:, :, None] * w[None, :, :]
            noise = rng.normal(0, SPEC['noise_sd'][view], (n, w.shape[1]))
            y = mu + parts.sum(axis=1) + noise
            var = pd.DataFrame(index=[f'{view}:feature_{j:03d}' for j in range(w.shape[1])])
            data[group][view] = ad.AnnData(y, obs=obs.copy(), var=var)
            teacher['contributions'][group][view] = parts
            teacher['noise'][group][view] = noise
            teacher['intercepts'][group][view] = mu
    return data, teacher

def save_canonical():
    """Explicit regeneration command; model notebooks only read these files."""
    import json
    data, teacher = simulate()
    observed = ROOT / 'data/observed'; hidden = ROOT / 'data/teacher'
    observed.mkdir(parents=True, exist_ok=True); hidden.mkdir(parents=True, exist_ok=True)
    provenance = {'specification': SPEC, 'measurements': 'Gaussian transformed abundance, not counts',
                  'preprocessing': 'Stored raw; feature centering and block RMS scaling at analysis time',
                  'generator': 'notebooks/course_utils.py:simulate', 'truth_used_for_fitting': False}
    (ROOT / 'data/provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    arrays = {}
    for v, w in teacher['weights'].items(): arrays[f'weights__{v}'] = w
    for g in data:
        arrays[f'scores__{g}'] = teacher['scores'][g].to_numpy()
        for v, a in data[g].items():
            a.write_h5ad(observed / f'{g}_{v}.h5ad')
            for key in ['contributions', 'noise', 'intercepts']:
                arrays[f'{key}__{g}__{v}'] = teacher[key][g][v]
    np.savez_compressed(hidden / 'truth.npz', **arrays)
    return data, teacher

def load_experiment():
    return {g: {v: ad.read_h5ad(ROOT / 'data/observed' / f'{g}_{v}.h5ad')
                for v in SPEC['features']} for g in SPEC['samples']}

def load_truth():
    arrays = np.load(ROOT / 'data/teacher/truth.npz')
    return {'scores': {g: pd.DataFrame(arrays[f'scores__{g}'],
                         index=[f'{g}_{i:03d}' for i in range(n)], columns=PROCESSES)
                       for g, n in SPEC['samples'].items()},
            'weights': {v: arrays[f'weights__{v}'] for v in SPEC['features']},
            **{key: {g: {v: arrays[f'{key}__{g}__{v}'] for v in SPEC['features']}
                      for g in SPEC['samples']} for key in ['contributions', 'noise', 'intercepts']}}

def make_mudata(views):
    # Reorder explicitly before constructing the aligned multiview container.
    ids = next(iter(views.values())).obs_names
    assert all(set(a.obs_names) == set(ids) for a in views.values())
    m = md.MuData({v: a[ids].copy() for v, a in views.items()})
    m.obs = next(iter(views.values())).obs.loc[m.obs_names].copy()
    return m

def pooled_views(data, center_within=False):
    result = {}
    for v in data['Asteron']:
        pieces = []
        for g in ['Asteron', 'Borealis']:
            a = data[g][v].copy()
            if center_within: a.X -= a.X.mean(axis=0)
            pieces.append(a)
        result[v] = ad.concat(pieces, join='inner')
    return result

def standardized(a):
    x = np.asarray(a.X, dtype=float)
    x = x - x.mean(axis=0)
    return x / np.sqrt(np.mean(x*x))  # one scalar per view, not feature z-scores

def heatmap(frame, title, cmap='viridis', vmin=None, vmax=None, annotate=False):
    frame = pd.DataFrame(frame)
    fig, ax = plt.subplots(figsize=(max(7, .95*frame.shape[1]), max(4.5, .5*frame.shape[0]+1.8)))
    im = ax.imshow(frame.to_numpy(), aspect='auto', cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_xticks(range(frame.shape[1]), frame.columns, rotation=35, ha='right')
    ax.set_yticks(range(frame.shape[0]), frame.index)
    if annotate:
        midpoint = ((vmin if vmin is not None else np.nanmin(frame)) +
                    (vmax if vmax is not None else np.nanmax(frame))) / 2
        for i in range(frame.shape[0]):
            for j in range(frame.shape[1]):
                val = frame.iloc[i, j]
                ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                        color='white' if val < midpoint else 'black', fontsize=11)
    ax.set_title(title); fig.colorbar(im, ax=ax, shrink=.8); fig.tight_layout()
    plt.show()

def crosscorr(left, right):
    left, right = left.align(right, join='inner', axis=0)
    c = np.corrcoef(left.to_numpy().T, right.to_numpy().T)[:left.shape[1], left.shape[1]:]
    return pd.DataFrame(c, index=left.columns, columns=right.columns)

def score_plot(scores, metadata, color='clinical_score', title='Sample factor scores'):
    metadata = metadata.loc[scores.index]
    fig, ax = plt.subplots()
    vals = metadata[color]
    if pd.api.types.is_numeric_dtype(vals):
        im = ax.scatter(scores.iloc[:,0], scores.iloc[:,1], c=vals, cmap='viridis', s=35)
        fig.colorbar(im, ax=ax, label=color)
    else:
        labels = [label for label in DISEASE_COLORS if label in vals.values] if color == 'disease' else vals.unique()
        for label in labels:
            mask = vals == label
            kwargs = {'color': DISEASE_COLORS[label]} if color == 'disease' else {}
            ax.scatter(scores.loc[mask].iloc[:,0], scores.loc[mask].iloc[:,1], label=label, **kwargs)
        ax.legend(title=color)
    ax.set(xlabel=scores.columns[0], ylabel=scores.columns[1], title=title)
    fig.tight_layout(); plt.show()

def weights_plot(weights, title='Feature weights (features × factors in the API)'):
    # Limit projected figures to 18 labelled features, selected within the supplied subset.
    selected = weights.abs().max(axis=1).nlargest(18).index
    shown = weights.loc[selected].T
    heatmap(shown, title + '\n18 strongest features in the displayed subset', cmap='RdBu_r',
            vmin=-np.abs(shown.to_numpy()).max(), vmax=np.abs(shown.to_numpy()).max())

def r2_plot(model):
    r = model.get_r2()
    table = r.pivot(index='component', columns=['group','view'], values='R2')
    table.columns = [f'{g} · {v}' for g, v in table.columns]
    heatmap(table, 'Single-factor reconstruction R² by group and view',
            vmin=0, vmax=1, annotate=True)
    return model.get_r2(type='total')

def diagnostics(model):
    loss = np.asarray(model.training_loss)
    fig, ax = plt.subplots(); ax.plot(loss)
    ax.set(xlabel='Epoch', ylabel='Stochastic negative ELBO (training loss)',
           title=f'{len(loss)} epochs; inspect trend and late fluctuations')
    fig.tight_layout(); plt.show()
    print('Finite loss:', np.isfinite(loss).all(), '| last-100 mean:', round(loss[-100:].mean(), 3))

def subspace_similarity(a, b):
    """Mean squared cosine of principal angles, invariant to basis rotations."""
    a, b = a.align(b, join='inner', axis=0)
    aa = a.to_numpy() - a.to_numpy().mean(0)
    bb = b.to_numpy() - b.to_numpy().mean(0)
    return float(np.mean(np.cos(subspace_angles(aa, bb))**2))

def schematic(kind='single'):
    rows = {'single': [('Asteron', 'RNA')],
            'separate': [('Asteron','RNA'),('Asteron','Protein'),('Borealis','RNA'),('Borealis','Protein')],
            'multiview': [('Asteron','RNA'),('Asteron','Protein')],
            'multigroup': [('Asteron','RNA'),('Asteron','Protein'),('Borealis','RNA'),('Borealis','Protein')]}[kind]
    fig, ax = plt.subplots(figsize=(13, 1.3*len(rows)+.7))
    for i,(g,v) in enumerate(rows):
        y = len(rows)-i-1; n=SPEC['samples'][g]; d=SPEC['features'][v]
        zname = f'Z {g}' if kind != 'separate' else f'Z {g},{v}'
        wname = f'W {v}' if kind != 'separate' else f'W {g},{v}'
        for x,w,label,c in [(0,3.0,f'Y {g},{v}\n{n} samples × {d} features',COLORS[v]),
                            (3.7,3.0,f'{zname}\n{n} samples × K factors',COLORS[g]),
                            (7.4,3.0,f'{wname}\nK factors × {d} features',COLORS[v])]:
            ax.add_patch(Rectangle((x,y),w,.75,facecolor=c,alpha=.16,edgecolor=c,lw=2))
            ax.text(x+w/2,y+.375,label,ha='center',va='center',fontsize=10)
        ax.text(3.35,y+.375,'≈',ha='center',va='center',fontsize=22)
        ax.text(7.05,y+.375,'×',ha='center',va='center',fontsize=22)
    ax.set(xlim=(-.1,10.5),ylim=(-.1,len(rows))); ax.axis('off')
    ax.set_title({'single':'Centered/scaled single table', 'separate':'Four independent coordinate systems',
                  'multiview':'Common sample coordinates; different feature spaces',
                  'multigroup':'Separate inhabitants; shared feature patterns across planets'}[kind])
    fig.tight_layout(); plt.show()

# Fixed classroom fit budget. Construction and fit calls remain in notebook cells.
FIT = dict(device='cpu', likelihoods='Normal', seed=42, save_path=False,
           max_epochs=1200, lr=.02, early_stopper_patience=250, batch_size=0,
           subset_var=None, plot_data_overview=False, update_every=-1, scale_elbo=True)

def export_fit(model, name):
    """Export small summaries for comparisons; never deserialize fitted Python objects."""
    out = ROOT / 'results' / name; out.mkdir(parents=True, exist_ok=True)
    for g,z in model.get_factors().items(): z.to_csv(out / f'scores_{g}.csv')
    for v,w in model.get_weights().items(): w.to_csv(out / f'weights_{v}.csv')
    model.get_r2(type='total').to_csv(out / 'r2.csv', index=False)
    np.save(out / 'loss.npy', np.asarray(model.training_loss))

def read_scores(name):
    out = ROOT / 'results' / name
    paths = sorted(out.glob('scores_*.csv'))
    if not paths: raise FileNotFoundError(f'Run the preceding practical to create {out}')
    return pd.concat([pd.read_csv(p, index_col=0) for p in paths])

def disease_association(z, obs):
    """Descriptive absolute point-biserial correlations, no inferential p-values."""
    y = obs.loc[z.index, 'disease'].eq('Diseased').astype(float).to_frame('Disease')
    return crosscorr(z, y).abs().iloc[:, 0]

def reconstruction_plot(x, estimate, title, figsize = (12, 3.2)):
    fig, axes = plt.subplots(1, 3, figsize= figsize)
    limit = np.quantile(np.abs(x), .98)
    for ax,a,label in zip(axes,[x,estimate,x-estimate],['Observed','Reconstructed','Residual']):
        im=ax.imshow(a,aspect='auto',cmap='RdBu_r',vmin=-limit,vmax=limit)
        ax.set(xlabel=f'{x.shape[1]} features',ylabel=f'{x.shape[0]} inhabitants',title=label)
    fig.suptitle(title); fig.colorbar(im, ax=axes, shrink=.65, label='Centered/scaled abundance')
    plt.show()

def truth_projection(scores, truth):
    """Training R² of each truth score projected onto the fitted score subspace."""
    scores, truth = scores.align(truth, join='inner', axis=0)
    a=scores.to_numpy()-scores.to_numpy().mean(0)
    b=truth.to_numpy()-truth.to_numpy().mean(0)
    pred=a @ np.linalg.lstsq(a,b,rcond=None)[0]
    return pd.Series(1-((b-pred)**2).sum(0)/(b*b).sum(0), index=truth.columns)

def generation_figures(data, teacher):
    fig, axes=plt.subplots(1,2,figsize=(12,4))
    for ax,g in zip(axes,SPEC['samples']):
        z=teacher['scores'][g]; obs=data[g]['RNA'].obs
        for label,offset in [('Healthy',-.15),('Diseased',.15)]:
            mask=obs.disease.eq(label)
            ax.bar(np.arange(6)+offset,z.loc[mask].mean(),width=.3,
                   yerr=z.loc[mask].std(),alpha=.75,label=label)
        ax.set_xticks(range(6),PROCESSES,rotation=35,ha='right')
        ax.set(title=g,ylabel='True score mean ± within-status SD'); ax.legend()
    fig.tight_layout(); plt.show()
    for v,w in teacher['weights'].items():
        heatmap(pd.DataFrame(w,index=PROCESSES,columns=[str(i) for i in range(w.shape[1])]).iloc[:,::3],
                f'True {v} weights: every third feature (full matrix saved)',cmap='RdBu_r',vmin=-1.5,vmax=1.5)

def probabilistic_schematic():
    fig,ax=plt.subplots(figsize=(12,4))
    labels=[(.0,1.8,'Priors\nZ: 80 × 6; W: 6 × 90'),(5.6,1.8,'Gaussian likelihood\nY: 80 × 90 around ZW'),
            (.0,.0,'Approximate posterior q\nMeans and uncertainty for Z, W'),(5.6,.0,'Numerical inference\nClippedAdam; learning rate lr')]
    for x,y,t in labels:
        ax.add_patch(Rectangle((x,y),5,1.1,facecolor='#377eb8',alpha=.12))
        ax.text(x+2.5,y+.55,t,ha='center',va='center')
    for a,b in [((5,2.35),(5.6,2.35)),((8.1,1.8),(8.1,1.1)),((5.6,.55),(5,.55))]:
        ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->'})
    ax.set(xlim=(-.1,10.7),ylim=(-.1,3.1));ax.axis('off');plt.show()
