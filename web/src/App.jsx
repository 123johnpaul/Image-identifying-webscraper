import { useMemo, useState } from 'react'
import './App.css'

const API_BASE = 'http://127.0.0.1:8000'

function App() {
  const [imageFile, setImageFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [description, setDescription] = useState('')
  const [identifyError, setIdentifyError] = useState('')
  const [compareMessage, setCompareMessage] = useState('Waiting for query…')
  const [metricPrice, setMetricPrice] = useState('$0.00')
  const [metricConfidence, setMetricConfidence] = useState('--')
  const [metricProvider, setMetricProvider] = useState('local_similarity')
  const [lastIdentify, setLastIdentify] = useState(null)

  const [allResults, setAllResults] = useState([])
  const [activeQuery, setActiveQuery] = useState('')

  const hasImage = useMemo(() => Boolean(imageFile), [imageFile])

  const setPreview = (file) => {
    setImageFile(file)
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
  }

  const handleIdentify = async () => {
    if (!imageFile) {
      setIdentifyError('Please upload an image first.')
      return
    }

    const formData = new FormData()
    formData.append('image', imageFile)
    if (description.trim()) {
      formData.append('description', description.trim())
    }

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

    // Explicitly grab the query we are about to send
    const queryToSend = lastIdentify.search_queries?.[0] || lastIdentify.product?.name || "Unknown item"
    setActiveQuery(queryToSend)

    const payload = {
      query: queryToSend,
      product: lastIdentify.product,
    }

    setCompareMessage(`Searching across UK stores for "${queryToSend}"...`)
    setAllResults([]) // Clear previous results

    try {
      const res = await fetch(`${API_BASE}/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      const data = await res.json()

      if (data.cheapest?.price) {
        setMetricPrice(`£${data.cheapest.price.toFixed(2)}`)
        setCompareMessage(`Cheapest found at ${data.cheapest.store ?? 'store'} for £${data.cheapest.price.toFixed(2)}`)
        setAllResults(data.all_results || [])
      } else {
        setCompareMessage('No products found matching that query.')
        setAllResults([])
      }
    } catch (err) {
      setCompareMessage(err.message)
    }
  }

  const handleReset = () => {
    setImageFile(null)
    setPreviewUrl('')
    setDescription('')
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
            Upload a product image, detect what it is, and compare prices across
            stores without seeing raw JSON debug output.
          </p>
          <div className="hero-actions">
            <button className="btn btn-ghost" onClick={() => setDescription('Red cotton shirt')}>
              Use sample description
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
              <p>Supported: JPG, PNG. Add a short description if needed.</p>
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
          <label className="label" htmlFor="description">Optional description</label>
          <textarea
            id="description"
            rows="3"
            placeholder="e.g. red shirt"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
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
          <h3>Price Comparison</h3>

          <button className="btn btn-primary" onClick={handleCompare} disabled={!lastIdentify}>
            {lastIdentify
              ? `Search stores for: "${lastIdentify.search_queries?.[0] || lastIdentify.product?.name}"`
              : 'Compare prices'
            }
          </button>
          <p className="muted" style={{ marginTop: '12px' }}>{compareMessage}</p>

          {/* Display the full list of scraped results */}
          {allResults.length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <h4 style={{ marginBottom: '10px' }}>All Store Results ({allResults.length})</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '400px', overflowY: 'auto' }}>
                {allResults.map((item, idx) => (
                  <div className="match-row" key={`${item.link}-${idx}`}>
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                      {item.image_url && (
                        <img src={item.image_url} alt="product" style={{ width: '40px', height: '40px', borderRadius: '6px', objectFit: 'cover' }} />
                      )}
                      <div>
                        <strong>{item.title.length > 40 ? item.title.substring(0, 40) + '...' : item.title}</strong>
                        <p className="muted small">{item.store}</p>
                      </div>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                      <span className="score">£{item.price.toFixed(2)}</span>
                      <a href={item.link} target="_blank" rel="noreferrer" className="muted small" style={{ textDecoration: 'underline' }}>View</a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>

      <footer className="footer">
        <span>Prototype UI · Structured product output</span>
      </footer>
    </div>
  )
}

export default App
