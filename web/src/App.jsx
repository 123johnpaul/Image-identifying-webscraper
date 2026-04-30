import { useMemo, useState } from 'react'
import './App.css'

const API_BASE = 'http://127.0.0.1:8000'

function App() {
  const [imageFile, setImageFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [formFields, setFormFields] = useState({
    product_name: '',
    category: '',
    brand: '',
    color: '',
  })
  const [identifyError, setIdentifyError] = useState('')
  const [compareMessage, setCompareMessage] = useState('Waiting for query…')
  const [metricPrice, setMetricPrice] = useState('$0.00')
  const [metricConfidence, setMetricConfidence] = useState('--')
  const [metricProvider, setMetricProvider] = useState('local_similarity')
  const [lastIdentify, setLastIdentify] = useState(null)

  const hasImage = useMemo(() => Boolean(imageFile), [imageFile])

  const setPreview = (file) => {
    setImageFile(file)
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
  }

  const hasMissingFields = () => {
    return Object.values(formFields).some((v) => !String(v).trim())
  }

  const handleIdentify = async () => {
    if (!imageFile) {
      setIdentifyError('Please upload an image first.')
      return
    }

    if (hasMissingFields()) {
      setIdentifyError('Please fill all required fields: name, category, brand, color.')
      return
    }

    const formData = new FormData()
    formData.append('image', imageFile)
    formData.append('product_name', formFields.product_name.trim())
    formData.append('category', formFields.category.trim())
    formData.append('brand', formFields.brand.trim())
    formData.append('color', formFields.color.trim())

    setIdentifyError('')

    try {
      const res = await fetch(`${API_BASE}/identify-product`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        throw new Error(`Identify failed: ${res.status}`)
      }

      const data = await res.json()
      setLastIdentify(data)
      setMetricConfidence(data.product?.confidence ? `${Math.round(data.product.confidence * 100)}%` : '--')
      setMetricProvider(data.debug?.provider ?? 'local_similarity')
    } catch (err) {
      setIdentifyError(err.message)
    }
  }

  const handleCompare = async () => {
    if (!lastIdentify) {
      setCompareMessage('Run identify first.')
      return
    }

    const payload = {
      query: lastIdentify.search_queries?.[0] || lastIdentify.product?.name,
      product: lastIdentify.product,
    }

    setCompareMessage('Comparing prices…')

    try {
      const res = await fetch(`${API_BASE}/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      const data = await res.json()
      if (data.cheapest?.price) {
        setMetricPrice(`$${data.cheapest.price}`)
        setCompareMessage(`Cheapest found at ${data.cheapest.store ?? 'store'} for $${data.cheapest.price}`)
      } else {
        setCompareMessage('Price comparison endpoint is still placeholder mode.')
      }
    } catch (err) {
      setCompareMessage(err.message)
    }
  }

  const handleReset = () => {
    setImageFile(null)
    setPreviewUrl('')
    setFormFields({
      product_name: '',
      category: '',
      brand: '',
      color: '',
    })
    setIdentifyError('')
    setCompareMessage('Waiting for query…')
    setMetricPrice('$0.00')
    setMetricConfidence('--')
    setMetricProvider('local_similarity')
    setLastIdentify(null)
  }

  const handleDrop = (event) => {
    event.preventDefault()
    const file = event.dataTransfer.files[0]
    if (file) {
      setPreview(file)
    }
  }

  const handleDragOver = (event) => {
    event.preventDefault()
  }

  const product = lastIdentify?.product
  const topMatches = lastIdentify?.debug?.top_matches || []

  return (
    <div className="page">
      <div className="bg-noise" />

      <header className="hero">
        <div className="hero-left">
          <p className="pill">Image | Identify | Compare</p>
          <h1>Find the lowest price from a single product photo.</h1>
          <p className="sub">
            Fill product fields, upload image, and compare prices with cleaner identification.
          </p>
          <div className="hero-actions">
            <button
              className="btn btn-ghost"
              onClick={() => setFormFields({
                product_name: 'Classic Shoulder Bag',
                category: 'Bag',
                brand: 'Channel',
                color: 'Blue',
              })}
            >
              Use sample fields
            </button>
            <button className="btn btn-muted" onClick={handleReset}>
              Reset
            </button>
          </div>
        </div>
        <div className="hero-card">
          <div className="metric">
            <span className="metric-label">Cheapest Found</span>
            <span className="metric-value">{metricPrice}</span>
          </div>
          <div className="metric">
            <span className="metric-label">Confidence</span>
            <span className="metric-value">{metricConfidence}</span>
          </div>
          <div className="metric">
            <span className="metric-label">Provider</span>
            <span className="metric-value">{metricProvider}</span>
          </div>
        </div>
      </header>

      <section className="panel">
        <div
          className={`uploader ${hasImage ? 'has-image' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
        >
          <div className="uploader-inner">
            <div className="uploader-preview">
              {previewUrl ? <img src={previewUrl} alt="preview" /> : <span>Drop image here</span>}
            </div>
            <div className="uploader-meta">
              <h2>Upload product image</h2>
              <p>All fields below are required.</p>
              <div className="uploader-actions">
                <label className="btn" htmlFor="imageInput">Choose image</label>
                <input
                  id="imageInput"
                  type="file"
                  accept="image/*"
                  hidden
                  onChange={(event) => {
                    const file = event.target.files[0]
                    if (file) {
                      setPreview(file)
                    }
                  }}
                />
                <button className="btn btn-primary" onClick={handleIdentify}>
                  Identify product
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="form">
          <label className="label">Product Name (required)</label>
          <input value={formFields.product_name} onChange={(e) => setFormFields({ ...formFields, product_name: e.target.value })} />
          <label className="label">Category (required: e.g. T-shirt)</label>
          <input value={formFields.category} onChange={(e) => setFormFields({ ...formFields, category: e.target.value })} />
          <label className="label">Brand (required)</label>
          <input value={formFields.brand} onChange={(e) => setFormFields({ ...formFields, brand: e.target.value })} />
          <label className="label">Color (required)</label>
          <input value={formFields.color} onChange={(e) => setFormFields({ ...formFields, color: e.target.value })} />
        </div>
      </section>

      <section className="results">
        <div className="result-card">
          <h3>Identified Product</h3>
          {!product && <p className="muted">Waiting for image...</p>}
          {identifyError && <p className="error">{identifyError}</p>}
          {product && (
            <div className="product-grid">
              <div><span className="k">Name</span><span>{product.name}</span></div>
              <div><span className="k">Category</span><span>{product.category || 'Unknown'}</span></div>
              <div><span className="k">Color</span><span>{product.color || 'Unknown'}</span></div>
              <div><span className="k">Brand</span><span>{product.brand || 'Unknown'}</span></div>
            </div>
          )}
          {lastIdentify?.search_queries?.length > 0 && (
            <div>
              <p className="muted">Search Queries</p>
              <div className="chips">
                {lastIdentify.search_queries.map((q) => <span className="chip" key={q}>{q}</span>)}
              </div>
            </div>
          )}
        </div>

        <div className="result-card">
          <h3>Top Visual Matches</h3>
          {topMatches.length === 0 && <p className="muted">No matches yet.</p>}
          {topMatches.slice(0, 4).map((m, idx) => (
            <div className="match-row" key={`${m.image_path}-${idx}`}>
              <div>
                <strong>{m.metadata?.title || 'Item'}</strong>
                <p className="muted small">{m.metadata?.category || 'Unknown'} • {m.metadata?.color || 'Unknown'}</p>
              </div>
              <span className="score">{Math.round((m.score || 0) * 100)}%</span>
            </div>
          ))}
          <button className="btn btn-primary" onClick={handleCompare}>
            Compare prices
          </button>
          <p className="muted">{compareMessage}</p>
        </div>
      </section>

      <footer className="footer">
        <span>Prototype UI · Structured mandatory input</span>
      </footer>
    </div>
  )
}

export default App
