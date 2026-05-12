[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20148312.svg)](https://doi.org/10.5281/zenodo.20148312)
# Directional Perturbation of Image Covariance Geometry

**Compression Response Across the Kodak Lossless True Color Suite**

> Directional covariance perturbation reduced Facebook pipeline JPEG output BPP by 29–87% across Kodak PCD0992.

Measurements across 72 directional perturbations of the Kodak Lossless True Color Image Suite, including manuscript PDF, per-image compression profiles, JSON datasets, and Facebook pipeline measurements.

Jasmine Baetzel (2026d)

---

## Overview

This is the fourth paper in a measurement series on inter-channel covariance geometry in the Kodak Lossless True Color Image Suite (PCD0992).

The Kodak images occupy highly structured, image-specific covariance geometries that interact imperfectly with fixed JPEG chrominance transforms. Previous papers characterized the baseline covariance structure ([statistical characterization](https://github.com/PearsonZero/kodak-pcd0992-statistical-characterization)), BT.601 decorrelation efficiency ([decorrelation gap](https://github.com/PearsonZero/kodak-pcd0992-bt601-decorrelation-gap)), and chrominance-axis misalignment geometry ([geometry of misalignment](https://github.com/PearsonZero/kodak-pcd0992-geometry-of-misalignment), [orthogonal constraint](https://github.com/PearsonZero/kodak-pcd0992-orthogonal-constraint)). Where those papers are observational, this paper is interventional — it applies directional covariance perturbation and measures the downstream compression response.

The perturbation operates in standard RGB pixel space upstream of any colorspace conversion. All 72 resulting images are standard files (JPEG, TIFF, or PNG) readable by any existing decoder without modification.

For each of the 24 Kodak images, three independent perturbations were applied targeting the red, green, and blue channel axes respectively. All 72 perturbed versions were measured through Facebook's JPEG recompression pipeline alongside unmodified originals. A control condition using the same pipeline without covariance perturbation did not produce comparable BPP reduction. Resolution change and format conversion alone did not reproduce the observed compression response.

---

## Key Results

| Metric | Original | Perturbed |
|---|---|---|
| Mean BPP (FB output) | 2.591 | 1.366 |
| Q60–Q90 spread (FB output) | 1.586 | 0.002 |
| Mean BPP reduction | — | 54.5% |
| Min BPP reduction | — | 29.1% |
| Max BPP reduction | — | 86.6% |

Under the measured FB2 pipeline, all 72 perturbed versions produced lower output BPP than their corresponding originals. All perturbed versions maintained lower FB output BPP despite a 7.1× higher output pixel count (2048×1366 vs. 768×512). BPP reduction is computed at output resolution, independent of input resolution differences. In all 24 images, perturbed versions exported at Q60 produced lower output BPP than originals exported at Q90 through the same pipeline.

The geometric displacement persists through repeated lossy encoding, retaining 84–97% of the initial displacement after seven rounds of JPEG recompression.

---

## File Structure

```

├── README.md
├── directional-perturbation-manuscript.pdf
├── profiles/
│   └── kodim01–kodim24_compression_profile.pdf (24 files, 3 pages each)
├── data/
│   ├── 768_OG_PNG/                  24 baseline JSONs (originals)
│   ├── 2560_JPG_SPDR/               72 pre-FB geometric JSONs
│   ├── Q90_JPG_SPDR_FB2/            72 FB2 steady-state measurements
│   ├── Q75_JPG_SPDR_FB2/            72 FB Q ladder
│   ├── Q60_JPG_SPDR_FB2/            72 FB Q ladder
│   ├── Q90_OG_PNG_FB2/              24 OG Q ladder through FB
│   ├── Q75_OG_PNG_FB2/              24 OG Q ladder through FB
│   ├── Q60_OG_PNG_FB2/              24 OG Q ladder through FB
│   ├── OG_PNG_FB2/                  24 OG baseline through FB
│   ├── ABC_JPG_SPDR_FB2/            24 control condition through FB
│   ├── OG_PNG_Q60_Q75_Q90/          72 direct export measurements
│   └── JPG_SPDR_Q60_Q75_Q90/        216 direct export measurements
└── scripts/
    ├── generate_pdfs_v2.py
    └── batch_measure.py
```

---

## Series

| Paper | Repository |
|---|---|
| Statistical Characterization | [kodak-pcd0992-statistical-characterization](https://github.com/PearsonZero/kodak-pcd0992-statistical-characterization) |
| BT.601 Decorrelation Gap | [kodak-pcd0992-bt601-decorrelation-gap](https://github.com/PearsonZero/kodak-pcd0992-bt601-decorrelation-gap) |
| Geometry of Misalignment | [kodak-pcd0992-geometry-of-misalignment](https://github.com/PearsonZero/kodak-pcd0992-geometry-of-misalignment) |
| Orthogonal Constraint | [kodak-pcd0992-orthogonal-constraint](https://github.com/PearsonZero/kodak-pcd0992-orthogonal-constraint) |
| **Directional Perturbation** | **this repository** |

---

## Citation

```
Baetzel, J. (2026d). Directional Perturbation of Image Covariance Geometry:
Compression Response Across the Kodak Lossless True Color Suite.
```

---

## References

[1] J. Baetzel, "Statistical Characterization of Inter-Channel Redundancy Structure in the Kodak Lossless True Color Image Suite," 2026.

[2] J. Baetzel, "Per-Image Decorrelation Efficiency of the BT.601 Fixed Transform," 2026.

[3] J. Baetzel, "The Geometry of Misalignment," 2026.

[4] J. Baetzel, "The Orthogonal Constraint on Chrominance Axis Misalignment," 2026.

---

Statistical analysis, measurements, and compression profiles by Jasmine Baetzel (2026).

Benchmark images from the Kodak Lossless True Color Image Suite (PCD0992), released by Eastman Kodak Company for unrestricted usage.
