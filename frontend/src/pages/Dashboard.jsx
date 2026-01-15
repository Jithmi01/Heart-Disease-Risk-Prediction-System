import React, { useEffect, useState } from "react";
import axios from "axios";
import { useTheme } from "../context/ThemeContext";

export default function Dashboard() {
  const { theme } = useTheme();
  const [predictions, setPredictions] = useState([]);

  useEffect(() => {
    const fetchPredictions = async () => {
      const res = await axios.get("http://localhost:5000/api/predictions");
      setPredictions(res.data);
    };
    fetchPredictions();
  }, []);

  const downloadReport = async (id) => {
    const res = await axios.get(`http://localhost:5000/api/generate-report/${id}`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `report_${id}.pdf`);
    document.body.appendChild(link);
    link.click();
  };

  return (
    <div className={`p-4 ${theme === "dark" ? "bg-gray-900 text-white" : "bg-gray-50 text-gray-900"}`}>
      <h1 className="text-xl font-bold mb-4">Past Predictions</h1>
      <table className="w-full border rounded">
        <thead>
          <tr>
            <th className="border p-2">Date</th>
            <th className="border p-2">Risk Level</th>
            <th className="border p-2">Probability</th>
            <th className="border p-2">Action</th>
          </tr>
        </thead>
        <tbody>
          {predictions.map(p => (
            <tr key={p._id}>
              <td className="border p-2">{new Date(p.created_at).toLocaleString()}</td>
              <td className="border p-2">{p.risk_level}</td>
              <td className="border p-2">{p.probability.toFixed(2)}%</td>
              <td className="border p-2">
                <button onClick={() => downloadReport(p._id)} className="bg-blue-600 text-white px-2 py-1 rounded">
                  Download PDF
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
