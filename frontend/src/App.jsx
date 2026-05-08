import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Activity, AlertCircle, CheckCircle, Clock } from 'lucide-react';

const API_URL = 'http://localhost:8000';

function App() {
  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [signals, setSignals] = useState([]);
  const [rcaForm, setRcaForm] = useState({ root_cause_category: 'Hardware', fix_applied: '', prevention_steps: '' });

  useEffect(() => {
    fetchIncidents();
    const interval = setInterval(fetchIncidents, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchIncidents = async () => {
    try {
      const res = await axios.get(`${API_URL}/incidents`);
      setIncidents(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchSignals = async (id) => {
    try {
      const res = await axios.get(`${API_URL}/incidents/${id}/signals`);
      setSignals(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSelectIncident = (inc) => {
    setSelectedIncident(inc);
    fetchSignals(inc.id);
  };

  const updateStatus = async (status) => {
    if (!selectedIncident) return;
    try {
      await axios.put(`${API_URL}/incidents/${selectedIncident.id}/status?status=${status}`);
      fetchIncidents();
      setSelectedIncident({ ...selectedIncident, status });
    } catch (err) {
      alert(err.response?.data?.detail || "Error updating status");
    }
  };

  const submitRCA = async (e) => {
    e.preventDefault();
    if (!selectedIncident) return;
    try {
      await axios.post(`${API_URL}/incidents/${selectedIncident.id}/rca`, rcaForm);
      fetchIncidents();
      setSelectedIncident({ ...selectedIncident, status: 'CLOSED' });
      alert("RCA submitted and incident closed.");
    } catch (err) {
      alert(err.response?.data?.detail || "Error submitting RCA");
    }
  };

  const getSeverityColor = (sev) => {
    switch(sev) {
      case 'P0': return 'bg-red-100 text-red-800 border-red-200';
      case 'P1': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'P2': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="bg-indigo-600 text-white p-4 shadow-md flex items-center justify-between">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Activity /> Mission-Critical IMS
        </h1>
        <div className="flex gap-4 text-sm font-medium">
          <span>Active Incidents: {incidents.filter(i => i.status !== 'CLOSED').length}</span>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Incident List */}
        <div className="md:col-span-1 bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col">
          <div className="p-4 border-b border-slate-200 bg-slate-50 font-semibold text-slate-700">
            Live Feed (Sorted by Severity)
          </div>
          <div className="overflow-y-auto flex-1 p-2 space-y-2 max-h-[80vh]">
            {incidents.map(inc => (
              <div 
                key={inc.id} 
                onClick={() => handleSelectIncident(inc)}
                className={`p-3 rounded-lg border cursor-pointer hover:shadow-md transition-shadow ${selectedIncident?.id === inc.id ? 'ring-2 ring-indigo-500 bg-indigo-50' : 'bg-white'} ${getSeverityColor(inc.severity)}`}
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="font-bold text-sm tracking-wide">{inc.component_id}</span>
                  <span className="px-2 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-white/50">{inc.severity}</span>
                </div>
                <div className="flex justify-between items-center text-xs opacity-80 font-medium">
                  <span>{inc.status}</span>
                  <span>{new Date(inc.created_at).toLocaleTimeString()}</span>
                </div>
              </div>
            ))}
            {incidents.length === 0 && (
              <div className="text-center p-8 text-slate-400 flex flex-col items-center">
                <CheckCircle className="w-8 h-8 mb-2 opacity-50" />
                <p>No active incidents</p>
              </div>
            )}
          </div>
        </div>

        {/* Incident Details & RCA */}
        <div className="md:col-span-2 space-y-6">
          {selectedIncident ? (
            <>
              {/* Actions & Status */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-2xl font-bold text-slate-800 mb-1">{selectedIncident.component_id}</h2>
                    <p className="text-slate-500 text-sm flex items-center gap-1">
                      <Clock className="w-4 h-4" /> Started at {new Date(selectedIncident.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div className={`px-3 py-1 rounded-full font-bold text-sm border ${getSeverityColor(selectedIncident.severity)}`}>
                    {selectedIncident.severity}
                  </div>
                </div>

                <div className="flex items-center gap-4 mb-6 p-4 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="font-semibold text-slate-700">Current Status:</span>
                  <span className="px-3 py-1 bg-white border border-slate-200 rounded-md shadow-sm font-medium text-slate-600">
                    {selectedIncident.status}
                  </span>
                </div>

                <div className="flex gap-3">
                  <button onClick={() => updateStatus('INVESTIGATING')} disabled={selectedIncident.status !== 'OPEN' && selectedIncident.status !== 'RESOLVED'} className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors">
                    Start Investigating
                  </button>
                  <button onClick={() => updateStatus('RESOLVED')} disabled={selectedIncident.status !== 'INVESTIGATING'} className="px-4 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 transition-colors">
                    Mark Resolved
                  </button>
                </div>
              </div>

              {/* RCA Form */}
              {selectedIncident.status === 'RESOLVED' && (
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden border-t-4 border-t-indigo-500">
                   <div className="p-4 border-b border-slate-100 bg-slate-50 font-semibold text-slate-800 flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-indigo-500" /> Mandatory Root Cause Analysis
                  </div>
                  <form onSubmit={submitRCA} className="p-6 space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Root Cause Category</label>
                      <select required className="w-full border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" value={rcaForm.root_cause_category} onChange={e => setRcaForm({...rcaForm, root_cause_category: e.target.value})}>
                        <option>Hardware Failure</option>
                        <option>Network Partition</option>
                        <option>Software Bug</option>
                        <option>Configuration Error</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Fix Applied</label>
                      <textarea required rows="3" className="w-full border border-slate-300 rounded-lg p-3 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" value={rcaForm.fix_applied} onChange={e => setRcaForm({...rcaForm, fix_applied: e.target.value})} placeholder="Describe what was done to resolve the issue..."></textarea>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Prevention Steps</label>
                      <textarea required rows="2" className="w-full border border-slate-300 rounded-lg p-3 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none" value={rcaForm.prevention_steps} onChange={e => setRcaForm({...rcaForm, prevention_steps: e.target.value})} placeholder="How to prevent this in the future..."></textarea>
                    </div>
                    <button type="submit" className="w-full py-3 bg-indigo-600 text-white rounded-lg font-bold shadow-md hover:bg-indigo-700 transition-colors">
                      Submit RCA & Close Incident
                    </button>
                  </form>
                </div>
              )}

              {/* Raw Signals Viewer */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="p-4 border-b border-slate-100 bg-slate-50 font-semibold text-slate-800 flex justify-between items-center">
                  <span>Raw Signals Context (Data Lake)</span>
                  <span className="text-xs bg-slate-200 text-slate-600 px-2 py-1 rounded-full">{signals.length} recent signals</span>
                </div>
                <div className="p-4 overflow-x-auto bg-slate-900 text-green-400 font-mono text-sm max-h-64 overflow-y-auto rounded-b-xl">
                  {signals.length === 0 ? (
                    <div className="text-slate-500 italic">No raw signals found or still loading...</div>
                  ) : (
                    signals.map((sig, i) => (
                      <div key={i} className="mb-2 pb-2 border-b border-slate-700/50">
                        <span className="text-slate-500">[{new Date(sig.timestamp).toISOString()}]</span> {sig.signal_type} <span className="text-blue-300">{JSON.stringify(sig.payload)}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="h-full min-h-[400px] flex items-center justify-center border-2 border-dashed border-slate-200 rounded-xl bg-slate-50 text-slate-400">
              <div className="text-center">
                <Activity className="w-12 h-12 mx-auto mb-3 opacity-20" />
                <p>Select an incident from the feed to view details</p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
