import React, { useEffect, useState } from "react";
import "../styles/Profile.css";
import axios from "axios";

const Profile = () => {
  const [details, setDetails] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios
      .get("http://localhost:8000/profile", { withCredentials: true })
      .then((response) => {
        setDetails(response.data);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching profile details:", error);
        setLoading(false);
      });
  }, []);

  return (
    <div className="profile-container">
      <h3>Profile</h3>
      {loading ? (
        <p>Loading...</p>
      ) : details ? (
        <div className="profile-details">
          <p>
            <strong>User ID:</strong> {details.user_id}
          </p>
          <p>
            <strong>Username:</strong> {details.username}
          </p>
          <p>
            <strong>Email:</strong> {details.email}
          </p>
          <p>
            <strong>Mobile:</strong> {details.mobile}
          </p>
        </div>
      ) : (
        <p>No profile data available.</p>
      )}
    </div>
  );
};

export default Profile;
