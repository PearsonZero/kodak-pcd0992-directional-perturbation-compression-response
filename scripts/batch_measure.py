#!/usr/bin/env python3
"""
batch_measure.py — Baetzel (2026) Series Measurement Pipeline
=============================================================
Usage:
    python3 batch_measure.py /path/to/folder/of/images
    python3 batch_measure.py /path/to/single_image.jpg

Output:
    ./batch_measure_output/  (created automatically)
    One JSON per image, named to match the source file.

Dependencies:
    Python 3, NumPy, Pillow
    pip install numpy Pillow
"""
import sys, os, json, hashlib, glob
import numpy as np
from PIL import Image

# ─── OUTPUT LOCATION ────────────────────────────────────────────
OUTPUT_DIR = os.path.join(os.getcwd(), "batch_measure_output")
# ────────────────────────────────────────────────────────────────

SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tif', '.tiff'}


def measure_image(filepath):
    """Measure a single image and return a dict of all metrics."""
    img = Image.open(filepath).convert('RGB')
    pixels = np.array(img, dtype=np.float64)
    h, w, _ = pixels.shape

    R = pixels[:, :, 0].flatten()
    G = pixels[:, :, 1].flatten()
    B = pixels[:, :, 2].flatten()

    n_pixels = h * w
    file_size = os.path.getsize(filepath)
    bpp = round((file_size * 8) / n_pixels, 3)

    # Pairwise Pearson correlations
    rg = np.corrcoef(R, G)[0, 1]
    rb = np.corrcoef(R, B)[0, 1]
    gb = np.corrcoef(G, B)[0, 1]
    avg_abs_r = round((abs(rg) + abs(rb) + abs(gb)) / 3, 4)

    # Covariance matrix → PCA
    data = np.vstack([R, G, B])
    cov = np.cov(data)
    eigenvalues, eigenvectors = np.linalg.eigh(cov)

    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    total_var = np.sum(eigenvalues)
    pc_pcts = [round(e / total_var * 100, 2) for e in eigenvalues]

    condition_number = round(eigenvalues[0] / eigenvalues[2], 2) if eigenvalues[2] > 0 else float('inf')

    # BT.601 reference vectors
    bt601_Y  = np.array([0.299, 0.587, 0.114])
    bt601_Cb = np.array([-0.169, -0.331, 0.500])
    bt601_Cr = np.array([0.500, -0.419, -0.081])

    def angle_between(v1, v2):
        cos_a = np.clip(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1, 1)
        return np.degrees(np.arccos(abs(cos_a)))

    theta1 = round(angle_between(eigenvectors[:, 0], bt601_Y), 2)
    theta2 = round(angle_between(eigenvectors[:, 1], bt601_Cb), 2)
    theta3 = round(angle_between(eigenvectors[:, 2], bt601_Cr), 2)

    # LOO deviation from regression: θ₃ = 1.004 × θ₂ − 2.372
    predicted_theta3 = 1.004 * theta2 - 2.372
    loo_dev = round(theta3 - predicted_theta3, 2)

    # Spatial autocorrelation (lag-1, average of H and V, per channel)
    def spatial_autocorr_channel(ch_2d):
        h_corr = np.corrcoef(ch_2d[:, :-1].flatten(), ch_2d[:, 1:].flatten())[0, 1]
        v_corr = np.corrcoef(ch_2d[:-1, :].flatten(), ch_2d[1:, :].flatten())[0, 1]
        return (h_corr + v_corr) / 2

    sa_r = spatial_autocorr_channel(pixels[:, :, 0])
    sa_g = spatial_autocorr_channel(pixels[:, :, 1])
    sa_b = spatial_autocorr_channel(pixels[:, :, 2])
    sa_avg = round((sa_r + sa_g + sa_b) / 3, 6)

    # SHA-256 of file
    with open(filepath, 'rb') as f:
        sha = hashlib.sha256(f.read()).hexdigest()

    # Channel statistics
    ch_stats = {}
    for name, ch in [('R', R), ('G', G), ('B', B)]:
        ch_stats[name] = {
            'mean': round(float(np.mean(ch)), 4),
            'std': round(float(np.std(ch)), 4),
            'min': int(np.min(ch)),
            'max': int(np.max(ch))
        }

    fmt = os.path.splitext(filepath)[1].upper().replace('.', '')
    if fmt == 'JPG': fmt = 'JPEG'
    if fmt == 'TIF': fmt = 'TIFF'

    return {
        'source_file': os.path.basename(filepath),
        'format': fmt,
        'resolution': f'{w}x{h}',
        'pixels': n_pixels,
        'file_size_bytes': file_size,
        'bpp': bpp,
        'correlations': {
            'R_G': round(rg, 6),
            'R_B': round(rb, 6),
            'G_B': round(gb, 6),
            'avg_abs_r': avg_abs_r
        },
        'channel_stats': ch_stats,
        'PC1_pct': pc_pcts[0],
        'PC2_pct': pc_pcts[1],
        'PC3_pct': pc_pcts[2],
        'eigenvalues': {
            'PC1': round(eigenvalues[0], 4),
            'PC2': round(eigenvalues[1], 4),
            'PC3': round(eigenvalues[2], 4)
        },
        'condition_number': condition_number,
        'theta2': theta2,
        'theta3': theta3,
        'loo_dev': loo_dev,
        'spatial_autocorrelation_avg': sa_avg,
        'sha256': sha
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 batch_measure.py <folder_or_file>")
        print(f"Output: {OUTPUT_DIR}/")
        sys.exit(1)

    path = sys.argv[1]

    # Gather image files
    if os.path.isfile(path):
        files = [path]
    elif os.path.isdir(path):
        files = sorted([
            os.path.join(path, f) for f in os.listdir(path)
            if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS
        ])
    else:
        print(f"ERROR: '{path}' is not a valid file or directory.")
        sys.exit(1)

    if not files:
        print(f"No supported images found in '{path}'")
        print(f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}")
        sys.exit(1)

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"{'='*60}")
    print(f"  Baetzel (2026) — Batch Measurement Pipeline")
    print(f"  Input:  {path} ({len(files)} image{'s' if len(files) != 1 else ''})")
    print(f"  Output: {OUTPUT_DIR}/")
    print(f"{'='*60}")

    for i, fp in enumerate(files, 1):
        fname = os.path.basename(fp)
        try:
            result = measure_image(fp)
            out_name = os.path.splitext(fname)[0] + '.json'
            out_path = os.path.join(OUTPUT_DIR, out_name)
            with open(out_path, 'w') as f:
                json.dump(result, f, indent=2)

            # Quick summary line
            c = result['correlations']
            bs = result['channel_stats']['B']
            print(f"  [{i:>3}/{len(files)}] {fname:<35} Avg|r|={c['avg_abs_r']:.4f}  BPP={result['bpp']:.3f}  B std={bs['std']:.1f}  ✓")

        except Exception as e:
            print(f"  [{i:>3}/{len(files)}] {fname:<35} ERROR: {e}")

    print(f"\n{'='*60}")
    print(f"  Done. {len(files)} JSON{'s' if len(files) != 1 else ''} written to:")
    print(f"  {OUTPUT_DIR}/")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
