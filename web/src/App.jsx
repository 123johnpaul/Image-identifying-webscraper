import { useMemo, useState } from 'react'
import './App.css'

const API_BASE = 'http://127.0.0.1:8000'

function App() {
  const [imageFile, setImageFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [description, setDescription] = useState('')
  const [identifyResult, setIdentifyResult] = useState('Waiting for image…')
  const [compareResult, setCompareResult] = useState('Waiting for query…')
  const [metricPrice, setMetricPrice] = useState('$0.00')
  const [metricConfidence, setMetricConfidence] = useState('--')
  const [metricProvider, setMetricProvider] = useState('mock')
  const [lastIdentify, setLastIdentify] = useState(null)

  const hasImage = useMemo(() => Boolean(imageFile), [imageFile])

  const setPreview = (file) => {
    setImageFile(file)
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
  }

  const handleIdentify = async () => {
    if (!imageFile) {
      setIdentifyResult('Please upload an image first.')
      return
    }

    const formData = new FormData()
    formData.append('image', imageFile)
    if (description.trim()) {
      formData.append('description', description.trim())
    }

    setIdentifyResult('Identifying product…')

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
      setIdentifyResult(JSON.stringify(data, null, 2))
      setMetricConfidence(data.product?.confidence ?? '--')
      setMetricProvider(data.debug?.provider ?? 'mock')
    } catch (err) {
      setIdentifyResult(err.message)
    }
  }

  const handleCompare = async () => {
    if (!lastIdentify) {
      setCompareResult('Run identify first.')
      return
    }

    const payload = {
      query: lastIdentify.search_queries?.[0] || lastIdentify.product?.name,
      product: lastIdentify.product,
    }

    setCompareResult('Comparing prices…')

    try {
      const res = await fetch(`${API_BASE}/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      const data = await res.json()
      setCompareResult(JSON.stringify(data, null, 2))
      if (data.cheapest?.price) {
        setMetricPrice(`$${data.cheapest.price}`)
      }
    } catch (err) {
      setCompareResult(err.message)
    }
  }

  const handleReset = () => {
    setImageFile(null)
    setPreviewUrl('')
    setDescription('')
    setIdentifyResult('Waiting for image…')
    setCompareResult('Waiting for query…')
    setMetricPrice('$0.00')
    setMetricConfidence('--')
    setMetricProvider('mock')
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

  return (
    <div className="page">
      <div className="bg-noise" />

      <header className="hero">
        <div className="hero-left">
          <p className="pill">Image → Identify → Compare</p>
          <h1>Find the lowest price from a single product photo.</h1>
          <p className="sub">
            Upload a product image, get a smart match, and compare prices across
            simulated retailers. Built for fast prototyping, ready for real data.
          </p>
          <div className="hero-actions">
            <button className="btn btn-ghost" onClick={() => setDescription('Nike Air Max black running shoe')}>
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
              <p>Supported: JPG, PNG. Add a description to boost results.</p>
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
            placeholder="e.g. Nike Air Max black running shoe"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
        </div>
      </section>

      <section className="results">
        <div className="result-card">
          <h3>Identified Product</h3>
          <pre>{identifyResult}</pre>
        </div>
        <div className="result-card">
          <h3>Price Comparison</h3>
          <pre>{compareResult}</pre>
          <button className="btn btn-primary" onClick={handleCompare}>
            Compare prices
          </button>
        </div>
      </section>

      <footer className="footer">
        <span>Prototype UI · Data and provider placeholders enabled</span>
      </footer>
    </div>
  )
}

export default App
