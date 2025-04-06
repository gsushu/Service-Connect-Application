// src/CreateRequest.js
import React, { useState } from "react";
import axios from "axios";
import "../styles/CreateRequest.css";

function CreateRequest() {
  const [serviceId, setServiceId] = useState(1);
  const [description, setDescription] = useState("");
  const [locationId, setLocationId] = useState(1);
  const [urgencyLevel, setUrgencyLevel] = useState("");
  const [additionalNotes, setAdditionalNotes] = useState("");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    const newRequest = {
      service_id: parseInt(serviceId, 10),
      description,
      location_id: parseInt(locationId, 10),
      urgency_level: urgencyLevel || null,
      additional_notes: additionalNotes || null,
    };

    try {
      const response = await axios.post(
        "http://localhost:8000/requests",
        newRequest,
        {
          withCredentials: true,
        }
      );
      setMessage(
        `Request created successfully: ${JSON.stringify(response.data)}`
      );
      setServiceId(1);
      setDescription("");
      setLocationId(1);
      setUrgencyLevel("");
      setAdditionalNotes("");
    } catch (error) {
      if (error.response) {
        setMessage(
          `Error creating request: ${
            error.response.data.detail || "Unknown error"
          }`
        );
      } else {
        setMessage(`Network error: ${error.message}`);
      }
    }
  };

  return (
    <div className="create-request-container">
      <h3>Create a New Request</h3>
      <form onSubmit={handleSubmit} className="create-request-form">
        <label>
          Service ID:
          <input
            type="number"
            value={serviceId}
            onChange={(e) => setServiceId(e.target.value)}
            required
          />
        </label>

        <label>
          Description:
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
          />
        </label>

        <label>
          Location ID:
          <input
            type="number"
            value={locationId}
            onChange={(e) => setLocationId(e.target.value)}
            required
          />
        </label>

        <label>
          Urgency Level (Optional):
          <input
            type="text"
            placeholder="e.g., High, Low"
            value={urgencyLevel}
            onChange={(e) => setUrgencyLevel(e.target.value)}
          />
        </label>

        <label>
          Additional Notes (Optional):
          <textarea
            value={additionalNotes}
            onChange={(e) => setAdditionalNotes(e.target.value)}
          />
        </label>

        <button type="submit">Submit Request</button>
      </form>
      {message && <p className="message">{message}</p>}
    </div>
  );
}

export default CreateRequest;
