import { useState } from "react";
import "./App.css";

function App() {
  const [region, setRegion] = useState("");
  const [sunlight, setSunlight] = useState("");
  const [soilType, setSoilType] = useState("");
  const [moisture, setMoisture] = useState("");

  const [hasSearched, setHasSearched] = useState(false);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    setLoading(true);
    setError("");
    setHasSearched(false);
    setRecommendations([]);

    try {
      const response = await fetch("http://127.0.0.1:8000/recommend", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          region,
          sunlight,
          soil_type: soilType,
          moisture,
        }),
      });

      if (!response.ok) {
        let errorMessage = "Unable to find recommendations.";

        try {
          const errorData = await response.json();

          if (errorData.detail) {
            errorMessage = errorData.detail;
          }
        } catch {
          // Keep default error message if response is not JSON.
        }

        throw new Error(errorMessage);
      }

      const data = await response.json();

      setRecommendations(data.recommendations);
      setHasSearched(true);
    } catch (error) {
      setError(error.message);
      setRecommendations([]);
      setHasSearched(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <main className="planner">
        <header className="hero">
          <p className="eyebrow">Native planting planner</p>

          <h1>Biodiversity & Native Planting Planner</h1>

          <p className="subtitle">
            Find native plants suited to your growing conditions
            and discover which pollinators they can support.
          </p>
        </header>

        <form className="planner-form" onSubmit={handleSubmit}>
          <label>
            Region
            <select
              value={region}
              onChange={(event) => setRegion(event.target.value)}
              required
            >
              <option value="">Select a region</option>
              <option value="Maryland Piedmont">
                Maryland Piedmont
              </option>
            </select>
          </label>

          <label>
            Sunlight
            <select
              value={sunlight}
              onChange={(event) => setSunlight(event.target.value)}
              required
            >
              <option value="">Select sunlight</option>
              <option value="full sun">Full Sun</option>
              <option value="part sun">Part Sun</option>
              <option value="shade">Shade</option>
            </select>
          </label>

          <label>
            Soil Type
            <select
              value={soilType}
              onChange={(event) => setSoilType(event.target.value)}
              required
            >
              <option value="">Select soil type</option>
              <option value="well-drained">Well-drained</option>
              <option value="clay">Clay</option>
              <option value="sandy">Sandy</option>
              <option value="loamy">Loamy</option>
            </select>
          </label>

          <label>
            Moisture
            <select
              value={moisture}
              onChange={(event) => setMoisture(event.target.value)}
              required
            >
              <option value="">Select moisture</option>
              <option value="dry">Dry</option>
              <option value="medium">Medium</option>
              <option value="wet">Wet</option>
            </select>
          </label>

          <button type="submit">
            Find My Plants
          </button>
        </form>

        {loading && (
          <p className="loading-message">
            Finding suitable native plants...
          </p>
        )}

        {error && (
          <p className="error">
            {error}
          </p>
        )}

        {!loading && !error && recommendations.length > 0 && (
          <section className="results">
            <div className="results-heading">
              <div>
                <p className="eyebrow">Your results</p>
                <h2>Top plant picks</h2>
              </div>

              <p className="result-count">
                {recommendations.length} plants
              </p>
            </div>

            <div className="plant-carousel">
              {recommendations.map((plant) => (
                <article
                  className="plant-card"
                  key={plant.species_id}
                >
                  <div className="plant-card-header">
                    <div>
                      <h3>{plant.common_name}</h3>

                      <p className="scientific-name">
                        {plant.scientific_name}
                      </p>
                    </div>
                  </div>

                  <div className="bloom">
                    <span className="bloom-label">Bloom period</span>
                    <strong>
                      {plant.bloom_start} – {plant.bloom_end}
                    </strong>
                  </div>

                  <div className="plant-details">
                    <div className="detail">
                      <span className="detail-label">☀ Sun</span>
                      <span>{plant.sun_needs}</span>
                    </div>

                    <div className="detail">
                      <span className="detail-label">🌱 Soil</span>
                      <span>{plant.soil_type}</span>
                    </div>

                    <div className="detail">
                      <span className="detail-label">💧 Moisture</span>
                      <span>{plant.moisture}</span>
                    </div>

                    <div className="detail">
                      <span className="detail-label">❄ Hardiness</span>
                      <span>{plant.hardiness_zones}</span>
                    </div>
                  </div>

                  <div className="pollinators">
                    <span className="detail-label">
                      Pollinators supported
                    </span>

                    <div className="pollinator-list">
                      {plant.pollinators_supported.map(
                        (pollinator) => (
                          <span
                            className="pollinator-tag"
                            key={pollinator}
                          >
                            {pollinator}
                          </span>
                        )
                      )}
                    </div>
                  </div>

                  <p className="native-label">
                    Native to {plant.native_range}
                  </p>
                </article>
              ))}
            </div>
          </section>
        )}

        {!loading &&
          !error &&
          recommendations.length === 0 &&
          hasSearched && (
            <p className="empty-message">
              No suitable plants found for your selected conditions.
            </p>
          )}
      </main>
    </div>
  );
}

export default App;