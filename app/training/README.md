# Local Product Similarity Training (CPU-Friendly)

This pipeline trains a local similarity model on `app/data` using Fashion Product Images metadata.

## Expected data

- `app/data/images/*.jpg` (or png)
- `app/data/styles.csv` (preferred) or `metadata.csv`/`labels.csv`

The loader auto-detects common column names (`id`, `articleType`, `baseColour`, `brandName`, `subCategory`).

## Install training dependencies

```bash
pip install -r requirements-training.txt
```

## Train

```bash
python -m app.training.train_similarity --data-dir app/data --epochs 4 --batch-size 32
```

Outputs:

- `app/models/similarity_v1/best.pt`
- `app/models/similarity_v1/summary.json`

## Build nearest-neighbor index

```bash
python -m app.training.build_index --data-dir app/data --checkpoint app/models/similarity_v1/best.pt
```

Output:

- `app/models/similarity_v1/index.npz`

## Test inference

```bash
python -m app.training.infer_similarity --image app/data/images/<some_image>.jpg --top-k 5
```

## Notes for 8GB RAM, no GPU

- Keep `batch-size` between `16` and `32`.
- Start with `epochs=3` then increase if needed.
- This is an embedding model for similarity retrieval, not exact SKU classification.

