# Methodology

**Measurement and Compression Pipeline for the Kodak PCD0992 Directional Perturbation Series**

Baetzel, J. (2026d)

---

## 1. Source Data

All 24 baseline images were obtained from the Kodak Lossless True Color Image Suite (PCD0992) in their standard base-resolution PNG format as distributed by Rich Franzen. These images originate from Kodak Photo CD disc PCD0992, scanned from 35mm photographic film (including Ektachrome and Kodachrome stocks) on the Kodak PCD Film Scanner 2000.

The scanner operated as a linear trilinear CCD device at 2048x3072 native resolution with 12-bit-per-channel analog-to-digital conversion [1]. Scanned data was transformed into Kodak's proprietary PhotoYCC color space — a luminance-chrominance decomposition designed to concentrate approximately 90% of image energy into the luminance channel while preserving an extended color gamut [4]. The base-resolution (768x512) layer was subsequently decoded to 8-bit-per-channel RGB for distribution as lossless PNG files.

The inter-channel correlation structure present in these images reflects the full imaging chain: film spectral sensitivity, scanner CCD response, PhotoYCC encoding coefficients, and the subsequent decode to 8-bit sRGB. This provenance is documented because any analysis of channel redundancy is implicitly operating on data shaped by these transformations.

For complete per-image statistical characterization of the baseline images, see [Statistical Characterization](https://github.com/PearsonZero/kodak-pcd0992-statistical-characterization) [2].

---

## 2. Computation Environment

All measurements were computed using Python 3 with the following libraries:

| Library | Version | Purpose |
|---|---|---|
| NumPy | 1.x | Array operations, covariance, correlation, eigendecomposition |
| Pillow (PIL) | 10.x | Image loading and pixel array extraction |

Images were loaded as 8-bit unsigned integer arrays and cast to 64-bit floating point prior to all computations. No preprocessing, normalization, or color space conversion was applied. All metrics were computed on the raw pixel values as distributed or as output by the measured pipeline.

---

## 3. Measurement Script

All per-image measurements were produced by `batch_measure.py`, included in the `scripts/` directory. The script accepts a folder of images or a single image file and outputs one JSON per image containing all computed metrics.

The same script was used across all datasets in this repository: baseline PNGs, perturbed JPEGs, direct quality exports, and Facebook pipeline outputs. This ensures measurement consistency across all conditions.

---

## 4. Published JSON Schema

Each JSON file contains the following fields:

**File metadata:**

`source_file` — Original filename. `format` — File format (JPEG, PNG, TIFF). `resolution` — Width × height in pixels. `pixels` — Total pixel count. `file_size_bytes` — File size on disk. `bpp` — Bits per pixel, computed as (file_size_bytes × 8) / pixels. `sha256` — SHA-256 hash of the source file.

**Inter-channel correlations:**

`correlations.R_G` — Pearson correlation between red and green channels.
`correlations.R_B` — Pearson correlation between red and blue channels.
`correlations.G_B` — Pearson correlation between green and blue channels.
`correlations.avg_abs_r` — Arithmetic mean of the absolute values of all three pairwise correlations: (|r(R,G)| + |r(R,B)| + |r(G,B)|) / 3. All correlation values are reported to six decimal places.

**Eigendecomposition:**

`PC1_pct`, `PC2_pct`, `PC3_pct` — Variance explained by each principal component as a percentage of total variance. Reported to two decimal places.

`eigenvalues.PC1`, `eigenvalues.PC2`, `eigenvalues.PC3` — Eigenvalues of the 3×3 RGB covariance matrix, sorted in descending order. Reported to four decimal places.

`condition_number` — Ratio of the largest to smallest eigenvalue (PC1/PC3). Measures the elongation of the color distribution ellipsoid in three-dimensional RGB space. Reported to two decimal places.

**Angular misalignment:**

`theta2` — Angle in degrees between the second eigenvector (PC2) and the BT.601 Cb axis.
`theta3` — Angle in degrees between the third eigenvector (PC3) and the BT.601 Cr axis.
Both reported to two decimal places.

`loo_dev` — Deviation from the LOO constraint regression line (θ₃ = 1.004 × θ₂ − 2.372) established in the [Orthogonal Constraint](https://github.com/PearsonZero/kodak-pcd0992-orthogonal-constraint) paper. Computed as θ₃(actual) − θ₃(predicted). Reported to two decimal places.

**Spatial autocorrelation:**

`spatial_autocorrelation_avg` — Mean lag-1 spatial autocorrelation across all three RGB channels, averaged over horizontal and vertical directions. Reported to six decimal places.

**Note on published data:** The `channel_stats` field (per-channel mean, standard deviation, min, max) is computed by the measurement script but has been removed from all published JSON files in this repository. All other fields are published as computed.

---

## 5. Covariance Matrix and Eigendecomposition

The 3×3 covariance matrix was computed using `numpy.cov` on the stacked channel arrays [R, G, B] with shape (3, N). NumPy computes the sample covariance matrix with N-1 denominator (Bessel's correction) by default. The covariance matrix uses Bessel's correction (N-1 denominator) while per-channel standard deviations use the population formula (N denominator), consistent with the methodology documented in the [Statistical Characterization](https://github.com/PearsonZero/kodak-pcd0992-statistical-characterization) paper [2].

Eigendecomposition was performed using `numpy.linalg.eigh`, which returns eigenvalues and eigenvectors for symmetric matrices. Eigenvalues were sorted in descending order and eigenvectors were reordered to match.

Pairwise Pearson correlations were computed using `numpy.corrcoef` on the stacked channel arrays, producing the normalized covariance.

---

## 6. BT.601 Angular Misalignment

Angular misalignment is computed as the acute angle between each image's eigenvectors and the corresponding BT.601 fixed-transform axes:

- θ₁: PC1 eigenvector vs. BT.601 Y axis [0.299, 0.587, 0.114]
- θ₂: PC2 eigenvector vs. BT.601 Cb axis [-0.169, -0.331, 0.500]
- θ₃: PC3 eigenvector vs. BT.601 Cr axis [0.500, -0.419, -0.081]

Angles are computed as the arccosine of the absolute value of the dot product between unit vectors, yielding values in the range [0°, 90°]. The absolute value ensures the measurement is sign-invariant (eigenvector direction ambiguity).

Only θ₂ and θ₃ are reported in the published JSONs. θ₁ is computed internally but not published.

---

## 7. Bits Per Pixel (BPP)

BPP is computed as:

```
BPP = (file_size_bytes × 8) / pixels
```

where `pixels` is the total pixel count (width × height) of the image as decoded. This measures the compressed file size normalized to the spatial resolution of the image.

For Facebook pipeline measurements, BPP is computed at the output resolution (typically 2048×1366 or 1366×2048), not the input resolution. This means the BPP reduction reported in the manuscript reflects compression efficiency at the pipeline's output stage, independent of any resolution difference between original and perturbed inputs.

---

## 8. Facebook Pipeline Protocol

Each image was uploaded to Facebook (Meta) via the standard web interface. Facebook re-encodes all uploaded images as JPEG at its own internally determined quality settings and resolution.

**FB1 and FB2 downloads:** After uploading, each image was downloaded from Facebook. This first download is designated FB1. The same image was then downloaded a second time without re-uploading, designated FB2. FB1 sometimes produced output that had not yet converged to the platform's final compression state. FB2 consistently returned steady-state output — a third or fourth download would produce identical results to FB2. All published measurements and manuscript values use FB2 steady-state downloads.

For original images at 768×512, FB1 and FB2 were identical (zero BPP jitter at Q60). For perturbed images at 2560×1707, FB1-to-FB2 jitter was small but nonzero — median approximately 0.015 BPP, maximum approximately 0.06 BPP across the Q90 set. This confirms FB2 as the correct measurement point.

**Output resolutions:** Facebook output perturbed images (input: 2560×1707) at 2048×1366 (landscape) or 1366×2048 (portrait). Six images — kodim04, kodim09, kodim10, kodim17, kodim18, kodim19 — were output in portrait orientation. The rotation was consistent across all three perturbation directions for each image (every RED, GRN, and BLU version of these six images was rotated identically). These six correspond to the portrait-orientation images in the original Kodak suite (512×768 rather than 768×512). The perturbation process preserves aspect ratio information that Facebook's pipeline appears to detect and respect. The exact mechanism is internal to Facebook's pipeline. All other perturbed images were output in landscape. Original baseline images (input: 768×512) were output at 768×512.

**Pipeline conditions:** All uploads and downloads were performed during May 2026. The specific compression parameters used by Facebook's pipeline are not publicly documented and may change over time. The measurements reported here reflect the pipeline's behavior during the measurement period.

---

## 9. Quality Ladder Protocol

To measure compression sensitivity across JPEG quality levels, each of the 24 images was exported at three quality settings — Q60, Q75, and Q90 — in both original and perturbed form.

**Direct export measurements** (`OG_PNG_Q60_Q75_Q90/` and `JPG_SPDR_Q60_Q75_Q90/`): These JSONs measure the images as exported locally, prior to any Facebook pipeline processing.

**FB quality ladder measurements** (`Q60_JPG_SPDR_FB2/`, `Q75_JPG_SPDR_FB2/`, `Q90_JPG_SPDR_FB2/` and corresponding OG folders): These JSONs measure the Facebook pipeline output for images that were exported at each quality level before upload.

The Q60–Q90 spread reported in the manuscript is computed as the difference between the mean FB output BPP at Q90 and the mean FB output BPP at Q60, across all images in the relevant condition (original or perturbed).

---

## 10. Control Condition (ABC)

A control condition was established in which images were processed through the identical pipeline — including resolution change and format conversion — without covariance perturbation. The control images are designated "ABC" in the dataset.

The control condition isolates whether the observed compression response is attributable to the covariance perturbation itself or to other aspects of the pipeline (resolution change, format conversion, recompression). Control images preserved their original correlation structure, remained on the LOO constraint manifold, and maintained their original dimensionality classification.

Control measurements are in `ABC_JPG_SPDR_FB2/` (24 JSONs, one per image).

---

## 11. Per-Image Compression Profiles

Twenty-four per-image compression profile PDFs are provided in the `profiles/` directory, one per Kodak image. Each profile is three pages:

**Page 1 — Geometric Displacement:** A 96-point scatter plot (θ₂ vs. θ₃) showing all 24 originals as gray dots, all 72 perturbations as faint colored dots (red/green/blue by direction), with the current image's original highlighted and its three perturbations labeled R/G/B. The LOO regression line (θ₃ = 1.004·θ₂ − 2.372, r = 0.9993) is shown as a dashed line. Below the scatter is a correlation table with four rows (Original, R-targeted, G-targeted, B-targeted) showing R-G, R-B, G-B, Avg|r|, θ₂, θ₃, and LOO deviation. Data source: `768_OG_PNG/` and `2560_JPG_SPDR/` JSONs.

**Page 2 — File Format and Size Comparison:** Two tables — original (PNG lossless, JPEG Q90/Q75/Q60) and redistributed (RED/GRN/BLU at Q60) — showing format, resolution, file size, BPP, and pixel count. Below is a horizontal bar chart comparing SPDR Q60 BPP against OG Q90 BPP. Data source: `768_OG_PNG/`, `OG_PNG_Q60_Q75_Q90/`, and `JPG_SPDR_Q60_Q75_Q90/` JSONs.

**Page 3 — FB Pipeline + Q Sensitivity:** Pipeline table showing OG PNG→FB, R/G/B-targeted→FB, and ABC control→FB with input resolution, output resolution, FB BPP, and BPP reduction percentage. Q sensitivity chart showing OG and SPDR BPP across Q60/Q75/Q90 through FB, with spread annotations. Per-image summary box with best direct BPP, best FB BPP, comparison to OG Q90→FB, and pixel ratio. Data source: all FB2 JSONs (OG, Q90 SPDR, ABC, Q ladder sets).

Profiles were generated by `generate_pdfs_v2.py` using matplotlib for figure rendering and ReportLab for PDF assembly. All plotted values are drawn directly from the published JSON datasets via pre-consolidated pickle files.

---

## 12. Dataset Summary

| Dataset | Folder | Count | Description |
|---|---|---|---|
| Baseline originals | `768_OG_PNG/` | 24 | Baseline measurements ([Statistical Characterization](https://github.com/PearsonZero/kodak-pcd0992-statistical-characterization)) |
| Pre-FB geometric | `2560_JPG_SPDR/` | 72 | Perturbed images before FB pipeline |
| FB2 steady-state (Q90) | `Q90_JPG_SPDR_FB2/` | 72 | Primary pipeline result |
| FB2 Q ladder (Q75) | `Q75_JPG_SPDR_FB2/` | 72 | Q sensitivity measurement |
| FB2 Q ladder (Q60) | `Q60_JPG_SPDR_FB2/` | 72 | Q sensitivity measurement |
| OG through FB (Q90) | `Q90_OG_PNG_FB2/` | 24 | Original Q ladder through FB |
| OG through FB (Q75) | `Q75_OG_PNG_FB2/` | 24 | Original Q ladder through FB |
| OG through FB (Q60) | `Q60_OG_PNG_FB2/` | 24 | Original Q ladder through FB |
| OG baseline through FB | `OG_PNG_FB2/` | 24 | Originals through FB pipeline |
| Control condition | `ABC_JPG_SPDR_FB2/` | 24 | No-perturbation control through FB |
| Direct export (OG) | `OG_PNG_Q60_Q75_Q90/` | 72 | Local exports at three quality levels |
| Direct export (SPDR) | `JPG_SPDR_Q60_Q75_Q90/` | 216 | Local exports at three quality levels |

Total: 720 published JSON files.

---

## 13. Reproducibility

The measurement pipeline (`batch_measure.py`) is deterministic. Given the same input images and the same Python environment, all computed metrics will reproduce exactly.

The Facebook pipeline measurements are not independently reproducible in the strict sense, because Facebook's compression parameters are not publicly documented and may change over time. The SHA-256 hash recorded in each JSON uniquely identifies the exact file that was measured, allowing verification that the published metrics correspond to specific downloaded files.

The per-image compression profile PDFs can be regenerated from the published JSON datasets using `generate_pdfs_v2.py`.

---

## References

[1] Eastman Kodak Company. Kodak Publication No. PCD-042, 1992.

[2] Baetzel, J. (2026a). "Statistical Characterization of Inter-Channel Redundancy Structure in the Kodak Lossless True Color Image Suite."

[3] Baetzel, J. (2026d). "Directional Perturbation of Image Covariance Geometry: Compression Response Across the Kodak Lossless True Color Suite."

[4] Giorgianni, E.J. and Madden, T.E. *Digital Color Management*. Addison-Wesley, 1998.
