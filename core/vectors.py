"""Deterministic vector mathematics for the core substrate.

Everything in this module is exact, deterministic arithmetic on
``numpy.ndarray`` — all randomness is injected by the caller via a seeded
generator, and the FFT used here is only a construction tool
(``np.fft.irfft`` is deterministic given its input).

Binding / unbinding
-------------------
We use a *circular convolution / correlation* binding scheme in the spirit
of Holographic Reduced Representations (Plate, 1995) — an independent
educational toy substrate, **not** an implementation of BDH or any
production memory system. The pair (bind, unbind) is what lets a
fixed-dimensional state carry key→value associations:

    bind(k, v)[i]  = sum_j k[j] * v[(i - j) mod d]     # store "k is v"
    unbind(x, k)   = bind(x, rev(k))                   # read out "?"

where ``rev(k)[i] = k[(-i) mod d]``. In the frequency domain, unbinding
multiplies by the complex conjugate of the key's spectrum.

**Keys are flat-spectrum vectors.** Every object key is built from random
Fourier phases with unit magnitude on every frequency, so ``|K(ω)|² = 1``
identically. Consequently

    bind(k, rev(k)) = delta        (exactly, up to float round-off)

which makes single-pair recall *exact*: unbinding a freshly written
binding with the correct key returns the value vector to machine
precision. This is what separates the *mechanism's* lossiness from the
*binding's* lossiness: with clean keys, all degradation visible in the
experiments is attributable to the state-update mechanism and to
interference between stored bindings — not to sloppy numerics.

Interference, concretely
------------------------
For a superposition ``x = sum_i bind(k_i, v_i)``, unbinding with ``k_q``
returns

    v_q + sum_{i != q} v_i ⊛ (k_i ⊛ rev(k_q))

Each cross-talk term is a phase-scrambled copy of another stored value.
Its energy is ~1 regardless of dimension, so the readout's cosine to the
true value shrinks like ``1/sqrt(n)`` with the number of stored pairs
(honest superposition capacity). When a competing key ``k_i`` is *similar*
to ``k_q`` (controlled by ``object_similarity``), the cross-talk term
retains a component along ``v_i`` proportional to the key similarity —
the "similar memories bleed into each other" phenomenon that the
interference mechanisms exaggerate or suppress.
"""

from __future__ import annotations

import numpy as np

EPS = 1e-12


def normalize(v: np.ndarray, eps: float = EPS) -> np.ndarray:
    """Return ``v / ||v||`` (or zeros when ``v`` is (near) zero)."""
    n = float(np.linalg.norm(v))
    if n <= eps:
        return np.zeros_like(v)
    return v / n


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors; 0.0 when either is zero."""
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    if na <= EPS or nb <= EPS:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def reverse(v: np.ndarray) -> np.ndarray:
    """``rev(v)[i] = v[(-i) mod d]`` — the convolution-inverse direction."""
    if v.shape[0] == 0:
        return v.copy()
    idx = np.concatenate([[0], np.arange(v.shape[0] - 1, 0, -1)])
    return v[idx]


# ---------------------------------------------------------------------------
# vector families
# ---------------------------------------------------------------------------
def random_unit_vector(rng: np.random.Generator, d: int) -> np.ndarray:
    """A unit-norm Gaussian vector (used for symbol *values*)."""
    return normalize(rng.standard_normal(d))


def flat_spectrum_vector(rng: np.random.Generator, d: int) -> np.ndarray:
    """A unit-norm vector with an exactly flat Fourier spectrum.

    Random phases on every frequency (unit magnitude), transformed back to
    the time domain. Used for object *keys* so that binding is exactly
    invertible (see module docstring).
    """
    n = d // 2
    if d % 2 == 0:
        K = np.zeros(n + 1, dtype=complex)
        K[0] = 1.0  # DC must be real
        if n >= 2:
            K[1:n] = np.exp(1j * rng.uniform(0.0, 2.0 * np.pi, size=n - 1))
        K[n] = 1.0  # Nyquist must be real
    else:
        K = np.zeros(n + 1, dtype=complex)
        K[0] = 1.0
        if n >= 1:
            K[1:] = np.exp(1j * rng.uniform(0.0, 2.0 * np.pi, size=n))
    k = np.fft.irfft(K, n=d)
    # Normalization preserves flatness (uniform scaling of the spectrum).
    return normalize(k)


def correlated_flat_vectors(
    rng: np.random.Generator, n: int, d: int, rho: float
) -> np.ndarray:
    """``n`` flat-spectrum keys with controlled *pairwise* cosine similarity.

    All keys are phase-perturbed versions of one shared random phase
    profile: ``phi_j(ω) = phi_base(ω) + eps_j(ω)`` with
    ``eps_j ~ N(0, -ln rho)``. Because only *phases* are perturbed, every
    key remains exactly flat-spectrum (single-pair recall stays exact even
    for very similar keys), while the expected pairwise cosine similarity
    is ``rho``:

        E[cos(k_i, k_j)] = E[e^{i(eps_i - eps_j)}] = e^{-sigma^2} = rho

    ``rho = 0`` → independent keys (essentially orthogonal);
    ``rho -> 1`` → nearly identical, maximally confusable keys.
    """
    rho = float(np.clip(rho, 0.0, 1.0))
    if rho <= 1e-9 or d < 4:
        # d < 4 leaves no free phases; keys are effectively independent anyway
        return np.array([flat_spectrum_vector(rng, d) for _ in range(n)])
    sigma = float(np.sqrt(-np.log(rho)))
    nf = (d // 2) - 1  # free phases (excluding DC and Nyquist)
    base = rng.uniform(0.0, 2.0 * np.pi, size=nf)

    def _one() -> np.ndarray:
        ph = base + rng.normal(0.0, sigma, size=nf)
        K = np.zeros(d // 2 + 1, dtype=complex) if d % 2 == 0 else np.zeros(d // 2 + 1, dtype=complex)
        K[0] = 1.0
        K[1 : 1 + nf] = np.exp(1j * ph)
        if d % 2 == 0:
            K[d // 2] = 1.0
        return normalize(np.fft.irfft(K, n=d))

    return np.array([_one() for _ in range(n)])


def correlated_vectors(
    rng: np.random.Generator, n: int, d: int, rho: float
) -> np.ndarray:
    """``n`` unit Gaussian vectors with expected pairwise cosine ``rho``.

    ``v_i = normalize(sqrt(rho) * base + sqrt(1 - rho) * w_i)`` with
    ``base`` and each ``w_i`` random unit vectors (``w_i`` orthogonal to
    ``base``). Since ``<v_i, v_j> = rho + (1 - rho) <w_i, w_j>`` and the
    ``w_i`` are mutually near-orthogonal, ``E[cos(v_i, v_j)] ≈ rho``.
    Used for symbol *values*, whose similarity makes competing symbols
    confusable. ``rho = 0`` → essentially orthogonal; ``rho -> 1`` → nearly
    identical values.
    """
    rho = float(np.clip(rho, 0.0, 1.0))
    base = random_unit_vector(rng, d)
    a = float(np.sqrt(rho))
    b = float(np.sqrt(max(0.0, 1.0 - rho)))
    out = np.empty((n, d))
    for i in range(n):
        w = random_unit_vector(rng, d)
        w = w - float(np.dot(w, base)) * base  # orthogonalize against base
        w = normalize(w)
        out[i] = normalize(a * base + b * w)
    return out


# ---------------------------------------------------------------------------
# binding
# ---------------------------------------------------------------------------
def bind(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Circular convolution ``a ⊛ b`` (commutative, exact O(d^2)).

    ``bind(a, b)[i] = sum_j a[j] * b[(i - j) mod d]``
    """
    d = a.shape[0]
    if b.shape[0] != d:
        raise ValueError(f"bind requires equal lengths, got {d} and {b.shape[0]}")
    out = np.zeros(d)
    for j in range(d):
        out += a[j] * np.roll(b, j)
    return out


def unbind(x: np.ndarray, key: np.ndarray) -> np.ndarray:
    """Read a value out of a bound state: ``unbind(x, key) = bind(x, rev(key))``.

    For a single stored binding ``x = bind(k, v)`` with a flat-spectrum
    key ``k`` this returns ``v`` exactly (see module docstring). For a
    superposition it returns ``v_q`` plus cross-talk from every other
    stored binding.
    """
    return bind(x, reverse(key))


def top_k_mask(x: np.ndarray, k: int) -> np.ndarray:
    """Binary mask keeping the ``k`` largest-|magnitude| entries of ``x``.

    Ties are broken by lower index, so the operation is fully deterministic.
    ``k`` is clamped to ``[1, d]``.
    """
    d = x.shape[0]
    k = int(max(1, min(k, d)))
    # argsort of -|x| is stable: equal values keep original (lower index) order.
    order = np.argsort(-np.abs(x), kind="stable")
    mask = np.zeros(d, dtype=bool)
    mask[order[:k]] = True
    return mask