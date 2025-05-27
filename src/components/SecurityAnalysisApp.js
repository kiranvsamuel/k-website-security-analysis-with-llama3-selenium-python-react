import React, { useState, useRef, useEffect } from 'react';
import { Chart, PieController, ArcElement, CategoryScale, LinearScale, BarController, BarElement, Tooltip, Legend, RadarController, PointElement, RadialLinearScale } from 'chart.js';

// Register Chart.js components
Chart.register(PieController, ArcElement, CategoryScale, LinearScale, BarController, BarElement, Tooltip, Legend, RadarController, PointElement, RadialLinearScale, LinearScale, CategoryScale);

// Error Boundary component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <div className="error-message">Component failed to load</div>;
    }
    return this.props.children;
  }
}

const RiskGauge = ({ score }) => {
  const gaugeRef = useRef(null);
  const chartInstance = useRef(null);




  useEffect(() => {
    if (gaugeRef.current) {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }

      const ctx = gaugeRef.current.getContext('2d');
      chartInstance.current = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: ['Risk Score', ''],
          datasets: [{
            data: [score, 100 - score],
            backgroundColor: [
              score >= 70 ? '#ff6384' : score >= 40 ? '#ffcd56' : '#4bc0c0',
              '#f0f0f0'
            ],
            borderWidth: 0
          }]
        },
        options: {
          circumference: 270,
          rotation: -135,
          cutout: '60%',
          animation: {
            animateScale: true,
            animateRotate: true,
            duration: 6000
          },
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              enabled: true,
              callbacks: {
                label: (context) => `${context.label}: ${context.raw}%`
              }
            },
            title: {
              display: true,
              text: 'Risk Assessment',
              font: {
                size: 16,
                weight: 'bold'
              }
            },
            centerText: {
              text: `${score}`,
              color: score >= 70 ? '#ff6384' : score >= 40 ? '#ffcd56' : '#4bc0c0',
              fontStyle: 'Arial',
              sidePadding: 20,
              minFontSize: 25,
              lineHeight: 25
            }
          }
        },
        plugins: [{
          id: 'centerText',
          beforeDraw(chart, args, options) {
            const { ctx, chartArea } = chart;
            if (!chartArea) return;
            
            ctx.save();
            const centerX = (chartArea.left + chartArea.right) / 2;
            const centerY = (chartArea.top + chartArea.bottom) / 2;
            
            ctx.font = `bold 60px ${options.fontStyle || 'Arial'}`;
            ctx.fillStyle = options.color || '#666';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(options.text, centerX, centerY);
            
            ctx.font = `30px ${options.fontStyle || 'Arial'}`;
            ctx.fillStyle = '#ff6384';
            ctx.fillText('Risk Score', centerX, centerY + 30);
            
            ctx.restore();
          }
        }]
      });
    }

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [score]);

  return <canvas ref={gaugeRef} />;
};


const TrackerBarChart = ({ data }) => {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    if (!data || !data.vendor_analysis) return;
    
    const reputations = {
      'known-good': 0,
      'neutral': 0,
      'known-bad': 0
    };

    Object.values(data.vendor_analysis).forEach(vendor => {
      if (vendor && vendor.reputation) {
        reputations[vendor.reputation]++;
      }
    });

    if (chartRef.current) {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }

      const ctx = chartRef.current.getContext('2d');
      chartInstance.current = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: ['Total Trackers', ...Object.keys(reputations)],
          datasets: [{
            label: 'Tracker Count',
            data: [data.risk_count, ...Object.values(reputations)],
            backgroundColor: [
              '#4e73df',
              '#1cc88a',
              '#f6c23e',
              '#e74a3b'
            ]
          }]
        },
        options: {
          scales: {
            y: { beginAtZero: true }
          }
        }
      });
    }

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [data]);

  return <canvas ref={chartRef} />;
};

const DataRadarChart = ({ data }) => {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    if (!data || !data.vendor_analysis) return;
    
    const dataTypes = {};
    Object.values(data.vendor_analysis).forEach(vendor => {
      if (vendor && Array.isArray(vendor.data_collected)) {
        vendor.data_collected.forEach(type => {
          dataTypes[type] = (dataTypes[type] || 0) + 1;
        });
      }
    });

    if (chartRef.current) {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }

      const ctx = chartRef.current.getContext('2d');
      chartInstance.current = new Chart(ctx, {
        type: 'radar',
        data: {
          labels: Object.keys(dataTypes),
          datasets: [{
            label: 'Data Collected',
            data: Object.values(dataTypes),
            backgroundColor: 'rgba(78, 115, 223, 0.2)',
            borderColor: 'rgba(78, 115, 223, 1)'
          }]
        }
      });
    }

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [data]);

  return <canvas ref={chartRef} />;
};

const PurposePieChart = ({ data }) => {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    if (!data || !data.vendor_analysis) return;
    
    const purposes = {};
    Object.values(data.vendor_analysis).forEach(vendor => {
      if (vendor && vendor.purpose) {
        purposes[vendor.purpose] = (purposes[vendor.purpose] || 0) + 1;
      }
    });

    if (chartRef.current) {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }

      const ctx = chartRef.current.getContext('2d');
      chartInstance.current = new Chart(ctx, {
        type: 'pie',
        data: {
          labels: Object.keys(purposes),
          datasets: [{
            data: Object.values(purposes),
            backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc']
          }]
        }
      });
    }

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [data]);

  return <canvas ref={chartRef} />;
};

const TrackerTable = ({ data }) => {
  if (!data || !data.vendor_analysis) return null;

  return (
    <div className="tracker-table">
      <table>
        <thead>
          <tr>
            <th>Domain</th>
            <th>Purpose</th>
            <th>Data Collected</th>
            <th>Reputation</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(data.vendor_analysis).map(([domain, info]) => (
            <tr key={domain}>
              <td>{domain}</td>
              <td>{info?.purpose || 'Unknown'}</td>
              <td>{info?.data_collected?.join(', ') || 'None'}</td>
              <td style={{
                color: info?.reputation === 'known-good' ? 'green' : 
                      info?.reputation === 'neutral' ? 'orange' : 'red'
              }}>
                {info?.reputation || 'unknown'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const TrackerDashboard = ({ data }) => {
  if (!data) return null;

  return (
    <div className="tracker-dashboard">
      <div className="dashboard-row">
        <div className="chart-container">
          <ErrorBoundary>
            <TrackerBarChart data={data} />
          </ErrorBoundary>
        </div>
        <div className="chart-container">
          <ErrorBoundary>
            <PurposePieChart data={data} />
          </ErrorBoundary>
        </div>
      </div>
      <div className="dashboard-row">
        <div className="chart-container">
          <ErrorBoundary>
            <DataRadarChart data={data} />
          </ErrorBoundary>
        </div>
      </div>
      <div className="dashboard-row">
        <ErrorBoundary>
          <TrackerTable data={data} />
        </ErrorBoundary>
      </div>
    </div>
  );
};

const IssuesActionsChart = ({ critical_issues, recommended_actions }) => {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    if (chartRef.current) {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }

      const ctx = chartRef.current.getContext('2d');
      chartInstance.current = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: ['Critical Issues', 'Recommended Actions'],
          datasets: [{
            label: 'Count',
            data: [critical_issues?.length || 0, recommended_actions?.length || 0],
            backgroundColor: [
              'rgba(255, 99, 132, 0.7)',
              'rgba(75, 192, 192, 0.7)'
            ],
            borderColor: [
              'rgba(255, 99, 132, 1)',
              'rgba(75, 192, 192, 1)'
            ],
            borderWidth: 1
          }]
        },
        options: {
          animation: { duration: 5000 },
          scales: {
            y: {
              beginAtZero: true,
              ticks: { stepSize: 1 }
            }
          },
          plugins: {
            title: {
              display: true,
              text: 'Issues vs Recommended Actions',
              font: { size: 16 }
            }
          }
        }
      });
    }

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [critical_issues, recommended_actions]);

  return <canvas ref={chartRef} />;
};

const SecurityLists = ({ critical_issues, recommended_actions }) => (
  <div className="security-lists">
    <div className="issues-list">
      <h3>Critical Issues</h3>
      <ul>
        {critical_issues?.map((issue, index) => (
          <li key={index} style={{ color: '#ff6384' }}>⚠️ {issue}</li>
        )) || <li>No critical issues found</li>}
      </ul>
    </div>
    <div className="actions-list">
      <h3>Recommended Actions</h3>
      <ul>
        {recommended_actions?.map((action, index) => (
          <li key={index} style={{ color: '#4bc0c0' }}>✅ {action}</li>
        )) || <li>No recommended actions</li>}
      </ul>
    </div>
  </div>
);

const SecurityDashboard = ({ assessment }) => {
  return (
    <div className="security-dashboard">
      <div className="dashboard-row">
        <div className="gauge-container">
          <RiskGauge score={assessment?.risk_score || 0} />
        </div>
      </div>
      <div className="lists-container">
        <SecurityLists 
          critical_issues={assessment?.critical_issues || []}
          recommended_actions={assessment?.recommended_actions || []}
        />
      </div>
    </div>
  );
};

const SecurityAnalysisApp = () => {
  const [url, setUrl] = useState('');
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [scanData, setScanData] = useState({
    pii: [],
    pii_risk_items: [],
    pii_risk_count: 0,
    pii_compliance_violations: [],
    summary_risk_score: 0,
    summary_critical_issues: [],
    summary_recommended_actions: [],
    trackers_risk_count: 0,
    trackers_domains: [],
    trackers_vendor_analysis: {},
    trackers_reputations: { 'known-good': 0, 'neutral': 0, 'known-bad': 0 },
    trackers_data_collected_summary: {},
    trackers_data_collected_keys: [],
    trackers_purpose: {},
    cookies_risk_count: 0,
    cookies_issues_by_type: {},
    cookies_high_risk_cookies: [],
    cookies: '0%',
    dropHouses: 0,
    trackers: [],
    mules: 0,
    localCache: '0%',
    trackersList: [],
    data_analysis: {}
  });

  const riskLevelChartRef = useRef(null);
  const piiTypeChartRef = useRef(null);
  const complianceChartRef = useRef(null);
  const riskLevelChart = useRef(null);
  const piiTypeChart = useRef(null);
  const complianceChart = useRef(null);

  const cookiesContainerRef = useRef(null);
  const trackersContainerRef = useRef(null);
  const localStorageContainerRef = useRef(null);
  // Auto-scroll effect 
  // Auto-scroll effect with no acceleration
useEffect(() => {
  if (!scanData.data_analysis) return;

  const scrollContainers = [
    { ref: cookiesContainerRef, condition: scanData.data_analysis?.cookies?.length > 0 },
    { ref: trackersContainerRef, condition: scanData.data_analysis?.trackers?.length > 0 },
    { ref: localStorageContainerRef, condition: Object.keys(scanData.data_analysis?.local_storage || {}).length > 0 }
  ];

  const scrollAllContainers = () => {
    scrollContainers.forEach(({ ref, condition }) => {
      if (condition && ref.current) {
        const container = ref.current;
        const scrollHeight = container.scrollHeight;
        const clientHeight = container.clientHeight;
        const maxScrollTop = scrollHeight - clientHeight;
        
        if (maxScrollTop > 0) {
          const duration = 95000; // 30 seconds duration
          const startTime = performance.now();
          
          const animateScroll = (currentTime) => {
            const elapsedTime = currentTime - startTime;
            const progress = Math.min(elapsedTime / duration, 1);
            
            // Pure linear progression - no acceleration
            const easeProgress = progress;
            
            container.scrollTop = easeProgress * maxScrollTop;
            
            if (progress < 1) {
              requestAnimationFrame(animateScroll);
            }
          };
          
          requestAnimationFrame(animateScroll);
        }
      }
    });
  };

  // Start scrolling all containers after a short delay (500ms)
  const scrollTimer = setTimeout(scrollAllContainers, 300);

  return () => {
    clearTimeout(scrollTimer);
  };
}, [scanData.data_analysis]);

  const handleScan = async () => {
    try {
      const response = await fetch('http://192.168.1.2:5002/api/v1/analyze_with_ollama', {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url })
      });
      setWebsiteUrl(url);

      if (!response.ok) throw new Error('Network response was not ok');

      const resp = await response.json();
      const data = resp.assesment || {};
      const data_analysis = resp.analysis || {};
      console.log('data_analysis:', data_analysis);

      
      // Process tracker data
      const reputationCounts = data.TRACKERS?.vendor_analysis ? 
        Object.values(data.TRACKERS.vendor_analysis).reduce((acc, vendor) => {
          const reputation = vendor?.reputation || 'neutral';
          acc[reputation] = (acc[reputation] || 0) + 1;
          return acc;
        }, { 'known-good': 0, 'neutral': 0, 'known-bad': 0 }) : 
        { 'known-good': 0, 'neutral': 0, 'known-bad': 0 };
console.log('reputationCounts:', reputationCounts);

      const dataCollectedCounts = data.TRACKERS?.vendor_analysis ? 
        Object.values(data.TRACKERS.vendor_analysis).reduce((acc, vendor) => {
          if (vendor?.data_collected) {
            vendor.data_collected.forEach(item => {
              acc[item] = (acc[item] || 0) + 1;
            });
          }
          return acc;
        }, {}) : {};
console.log('dataCollectedCounts:', dataCollectedCounts);
      
      const purposeCounts = data.TRACKERS?.vendor_analysis ? 
        Object.values(data.TRACKERS.vendor_analysis).reduce((acc, vendor) => {
          const purpose = vendor?.purpose || 'Unknown';
          acc[purpose] = (acc[purpose] || 0) + 1;
          return acc;
        }, {}) : {};
console.log('purposeCounts:', purposeCounts);
      setScanData({ 
        pii: Array.isArray(data.PII?.risk_items) ? data.PII.risk_items.map((_, i) => i + 1) : [],
        pii_risk_count: data.PII?.risk_count || 0,
        pii_risk_items: Array.isArray(data.PII?.risk_items) ? data.PII.risk_items : [],
        pii_compliance_violations: Array.isArray(data.PII?.compliance_violations) ? data.PII.compliance_violations : [],
        summary_risk_score: data.OVERALL_SECURITY_ASSESSMENT?.risk_score || 0,
        summary_critical_issues: Array.isArray(data.OVERALL_SECURITY_ASSESSMENT?.critical_issues) ? data.OVERALL_SECURITY_ASSESSMENT.critical_issues : [],
        summary_recommended_actions: Array.isArray(data.OVERALL_SECURITY_ASSESSMENT?.recommended_actions) ? data.OVERALL_SECURITY_ASSESSMENT.recommended_actions : [],
        trackers_risk_count: data.TRACKERS?.risk_count || 0,
        trackers_domains: Array.isArray(data.TRACKERS?.domains) ? data.TRACKERS.domains : [],
        trackers_vendor_analysis: data.TRACKERS?.vendor_analysis || {},
        trackers_reputations: reputationCounts,
        trackers_data_collected_summary: dataCollectedCounts,
        trackers_data_collected_keys: Object.keys(dataCollectedCounts),
        trackers_purpose: purposeCounts,
        cookies_risk_count: data.COOKIES?.risk_count || 0,
        cookies_issues_by_type: data.COOKIES?.issues_by_type || {},
        cookies_high_risk_cookies: data.COOKIES?.high_risk_cookies || [],
        cookies: `${data.COOKIES?.length || data.COOKIES?.risk_count || 0},${Math.min((data.COOKIES?.length || data.COOKIES?.risk_count || 0) * 10, 100)}%`,
        dropHouses: data.DROP_HOUSES?.risk_count || 0,
        trackers: [data.TRACKERS?.risk_count || 0],
        mules: data.MULES?.risk_count || 0,
        localCache: `${Math.min((data.LOCAL_CACHE?.risk_count || 0) * 30, 100)}%`,
        trackersList: data.TRACKERS?.domains || [],
        data_analysis : data_analysis
      });
console.log('trackers_data_collected_keys:', Object.keys(dataCollectedCounts));
    } catch (error) {
      console.error('Scan failed:', error);
      alert('Scan failed. Check console for details.');
    }
  };

  const processPiiData = (riskItems) => {
    if (!Array.isArray(riskItems)) return { riskLevels: {}, piiTypes: {} };
    
    const riskLevels = riskItems.reduce((acc, item) => {
      const level = item.risk_level?.toLowerCase() || 'unknown';
      acc[level] = (acc[level] || 0) + 1;
      return acc;
    }, {});

    const piiTypes = riskItems.reduce((acc, item) => {
      const type = item.type || 'Unknown';
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {});

    return { riskLevels, piiTypes };
  };

  useEffect(() => {
    if (!scanData.pii_risk_items.length) return;

    const { riskLevels, piiTypes } = processPiiData(scanData.pii_risk_items);

    // Risk Level Pie Chart
    if (riskLevelChartRef.current) {
      if (riskLevelChart.current) riskLevelChart.current.destroy();
      
      const ctx = riskLevelChartRef.current.getContext('2d');
      riskLevelChart.current = new Chart(ctx, {
        type: 'pie',
        data: {
          labels: Object.keys(riskLevels),
          datasets: [{
            data: Object.values(riskLevels),
            backgroundColor: ['#ef4444', '#f97316', '#3b82f6', '#6b7280'],
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: { duration: 2000 },
          plugins: {
            title: {
              display: true,
              text: 'PII Risk Level Distribution',
              font: { size: 14 }
            },
            legend: { position: 'bottom' }
          }
        }
      });
    }

    // PII Type Bar Chart
    if (piiTypeChartRef.current) {
      if (piiTypeChart.current) piiTypeChart.current.destroy();
      
      const ctx = piiTypeChartRef.current.getContext('2d');
      piiTypeChart.current = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: Object.keys(piiTypes),
          datasets: [{
            label: 'Count',
            data: Object.values(piiTypes),
            backgroundColor: '#3b82f6',
            borderWidth: 1
          }]
        },
        options: {
          animation: { duration: 2000 },
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: 'PII Type Distribution',
              font: { size: 14 }
            },
            legend: { display: false }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: { stepSize: 1 }
            }
          }
        }
      });
    }

    // Compliance Violations Donut Chart
    if (complianceChartRef.current && scanData.pii_compliance_violations.length > 0) {
      if (complianceChart.current) complianceChart.current.destroy();
      
      const complianceCounts = scanData.pii_compliance_violations.reduce((acc, violation) => {
        acc[violation] = (acc[violation] || 0) + 1;
        return acc;
      }, {});

      const ctx = complianceChartRef.current.getContext('2d');
      complianceChart.current = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: Object.keys(complianceCounts),
          datasets: [{
            data: Object.values(complianceCounts),
            backgroundColor: ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6'],
            borderWidth: 1
          }]
        },
        options: {
          animation: { duration: 3000 },
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: 'Compliance Violations',
              font: { size: 14 }
            },
            legend: { position: 'bottom' }
          }
        }
      });
    }
  }, [scanData]);

  useEffect(() => {
    return () => {
      if (riskLevelChart.current) riskLevelChart.current.destroy();
      if (piiTypeChart.current) piiTypeChart.current.destroy();
      if (complianceChart.current) complianceChart.current.destroy();
    };
  }, []);

  const renderRiskItems = (items) => {
    if (!Array.isArray(items) || items.length === 0) {
      return <span className="text-sm text-gray-500">No risk items found</span>;
    }
    return (
      <ul className="list-disc pl-5">
        {items.map((item, index) => {
          if (!item || typeof item !== 'object') return null;
          
          const { field = 'Unknown', type = 'Unknown', risk_level = 'Unknown', evidence = 'None' } = item;
          
          let riskColor;
          switch (risk_level.toLowerCase()) {
            case 'high': riskColor = 'text-red-600'; break;
            case 'medium': riskColor = 'text-yellow-600'; break;
            case 'low': riskColor = 'text-blue-600'; break;
            default: riskColor = 'text-gray-600';
          }
          
          return (
            <li key={index} className="text-sm mb-1">
              <span className="text-purple-600 font-bold">{field}</span> - {type} - {evidence} (
                <span className={`font-semibold ${riskColor}`}>
                  {risk_level} risk
                </span>
              )
            </li>
          );
        })}
      </ul>
    );
  };

  const renderArrayItems = (items) => {
  if (!Array.isArray(items)) {
    return <span className="text-sm text-gray-500">Invalid data</span>;
  }
  
  if (items.length === 0) {
    return <span className="text-sm text-gray-500">No items found</span>;
  }
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item, index) => {
        if (!item) return null;
        
        return (
          <span 
            key={index}
            style={{
              backgroundColor: 'LemonChiffon', 
              paddingLeft: '15px',
              paddingRight: '15px',
              paddingTop: '5px',
              paddingBottom: '5px',
              borderRadius: '5px', 
              color: 'red',
              marginRight: '5px',
              marginBottom: '5px'
            }}
          >
            <strong>{item}</strong>
          </span>
        );
      })}
    </div>
  );
};



  const renderTrackersList = () => {
    if (!Array.isArray(scanData.trackersList) || scanData.trackersList.length === 0) {
      return <span className="text-sm text-gray-500">No trackers found</span>;
    }

    return (
      <ul className="list-disc pl-5">
        {scanData.trackersList.map((tracker, index) => (
          <li key={index} className="text-sm">{tracker}</li>
        ))}
      </ul>
    );
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="bg-white p-6 rounded-lg shadow-md mb-6" style={{ backgroundColor: 'DarkSlateBlue'}} >
        <h1 className="text-2xl font-bold text-gray-800 mb-4" style={{ backgroundColor: 'DarkSlateBlue', color: 'white' }} >K-Website Security Analysis</h1>
        <div className="flex flex-col sm:flex-row gap-2">
          <input
            type="text"
            placeholder="Enter website URL"
            className="flex-1 p-2 rounded border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <button
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors" 
            style={{ color: 'DarkSlateBlue', backgroundColor: 'LightCyan' }} 
            onClick={handleScan}
          >
            Scan
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
        {/* Overall Summary*/}
        <div className="bg-white p-4 rounded-lg shadow md:col-span-1 lg:col-span-2 row-span-2" >
          <table className="w-full" style={{ padding: '5px', width: '100%' }}>
            <tbody>
              <tr>
                <td colSpan="4" className="font-bold text-lg p-2 center">
                  <div id='websitename' style={{ 
                  color: 'DarkSlateBlue',
                  fontSize: '20pt', 
                  borderRadius: '2.5px', 
                  textAlign: 'center', 
                  padding: '20px' 
                }}>{websiteUrl || 'Enter URL and click Scan'}
                </div>    
                  <SecurityDashboard assessment={{
                    risk_score: scanData.summary_risk_score,
                    critical_issues: scanData.summary_critical_issues,
                    recommended_actions: scanData.summary_recommended_actions 
                  }} />
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* PII Section */}
        <div className="bg-white p-4 rounded-lg shadow md:col-span-2 lg:col-span-2">
          <table className="w-full" style={{ padding: '5px' }}>
            <tbody>
              <tr>
                <td style={{ 
                  backgroundColor: 'DarkSlateBlue', 
                  color: 'white', 
                  borderRadius: '7.5px' 
                }} colSpan="3" className="font-bold text-lg p-2">
                  Personally Identifiable Information (PII)
                </td>
              </tr>
              <tr>
                <td className="py-2"><strong style={{color:'DarkSlateBlue'}}>Risk Count:</strong></td>
                <td className="py-2"><span style={{fontSize:"15pt", backgroundColor:'MediumVioletRed', paddingLeft:'20px',paddingRight:'20px', padding:'5px', borderRadius :'5px', color:'white'}}>
                  <strong > {scanData.pii_risk_count} </strong></span></td>
              </tr>
              <tr> 
                <td className="py-2 align-top"><strong style={{color:'DarkSlateBlue'}}>Risk Items:</strong></td>
                <td className="py-2" colSpan="2">
                  {renderRiskItems(scanData.pii_risk_items)}
                </td>
              </tr>
              <tr>
                <td className="py-2 align-top"><strong style={{color:'DarkSlateBlue'}}>Compliance violations:</strong></td>
                <td className="py-2" colSpan="2"><span style={{ backgroundColor:"orange", padding:"5px" }}>
                  {scanData.pii_compliance_violations.length 
                    ? scanData.pii_compliance_violations.join(', ') 
                    : 'None'}
                    </span>
                </td>
              </tr>
              <tr>
                <td colSpan="3" className="pt-4">
                  <div className="grid grid-cols-3 gap-4 w-full">
                    <div className="chart-container" style={{ height: '230px' }}>
                      <center>PII Type</center>
                      <canvas ref={piiTypeChartRef}></canvas>
                    </div>
                    <div className="chart-container" style={{ height: '230px' }}>
                      <center>Risk Level</center>
                      <canvas ref={riskLevelChartRef}></canvas>
                    </div>
                    {scanData.pii_compliance_violations.length > 0 && (
                      <div className="chart-container" style={{ height: '230px' }}>
                        <center>Compliance</center>
                        <canvas ref={complianceChartRef}></canvas>
                      </div>
                    )}
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* TRACKERS */}
        <div className="bg-white p-4 rounded-lg shadow md:col-span-2 lg:col-span-2">
          <table className="w-full" style={{ padding: '5px' }}>
            <tbody>
              <tr>
                <td style={{ backgroundColor: 'DarkSlateBlue', color: 'white', borderRadius: '7.5px' }} 
                    colSpan="3" 
                    className="font-bold text-lg p-2" >
                    Trackers
                  </td>
              </tr>
              <tr>
                <td className="py-2"><strong style={{color:'DarkSlateBlue'}}>Risk Count:</strong></td>
                <td className="py-2"><span className="text-lg text-red-600 " 
                style={{ fontSize:"15pt", backgroundColor:'MediumVioletRed', paddingLeft:'20px',paddingRight:'20px', padding:'5px', borderRadius :'5px', color:'white'}}>
                  <strong>{scanData.trackers_risk_count}</strong></span></td>
              </tr>
              <tr> 
                <td className="py-2 align-top"><strong style={{color:'DarkSlateBlue'}}>Domains:</strong></td>
                <td className="py-2"  colSpan="2" >
                 <ul className="list-disc pl-5">                 
                          {
                          scanData.trackers_domains.map((item, index) => {
                            if (!item) return null;

                            return (
                               <li key={index} className="text-sm text-purple-600 font-bold break-words max-w-xs">
                                <span className="text-purple-600 font-bold">{item}</span>
                              </li>
                            );
                          })}
                  </ul>
                </td>
              </tr>
              <tr>
                <td colSpan="3"><strong >Data Collected:</strong></td>
              </tr>
              <tr>
                <td className="py-2"  colSpan="3" >
                  {renderArrayItems(scanData.trackers_data_collected_keys)}
                </td>
              </tr>
              <tr>
                <td colSpan="3"><strong >Tracker(s) Purpose:</strong>{renderArrayItems(Object.keys(scanData.trackers_purpose))}</td>
              </tr>
              <tr>
                <td className="py-2"  colSpan="3" >
                  <strong>Trackers List:</strong>
                </td>
              </tr>
              <tr>
                <td className="py-2" colSpan="3">
                  {scanData.data_analysis?.trackers?.length > 0 ? (
                    <div id="dvTrackers" 
                          ref={trackersContainerRef}
                          className="font-mono text-sm bg-black p-2 rounded overflow-y-scroll max-h-60 w-full text-green-400 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-900"
                        >
                      {scanData.data_analysis.trackers.map((tracker, index) => (
                        <div 
                          key={index} 
                          className="mb-3 break-all whitespace-pre-wrap overflow-hidden"
                          style={{ wordBreak: 'break-word' }}
                        >
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                            <div><span className="font-semibold text-green-300">Type:</span> <span className="text-green-400">{tracker.type}</span></div>
                            <div><span className="font-semibold text-green-300">Source:</span> <span className="text-green-400">{tracker.source}</span></div>
                            <div><span className="font-semibold text-green-300">Risk:</span> <span className="break-all text-green-400">{tracker.risk}</span></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span className="text-sm text-gray-500">No Trackers found</span>
                  )}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* COOKIES */}
        <div className="bg-white p-4 rounded-lg shadow md:col-span-2 lg:col-span-2">
          <table className="w-full" style={{ padding: '5px' }}>
            <tbody>
              <tr>
                <td style={{ backgroundColor: 'DarkSlateBlue', color: 'white', borderRadius: '7.5px' }} 
                    colSpan="2" 
                    className="font-bold text-lg p-2" >
                    Cookies
                  </td>
              </tr>
              <tr>
                <td className="py-2"><strong style={{color:'DarkSlateBlue'}}>High Risk Count: </strong> 
                <span className="text-lg text-red-600 " 
                style={{fontSize:"15pt", backgroundColor:'MediumVioletRed', paddingLeft:'20px',paddingRight:'21px', padding:'5px', borderRadius :'5px', left:"10px", color:'white'}}>
                  <strong>{scanData.cookies_risk_count}</strong></span>
                </td>
                <td className="py-2"> </td>
              </tr>
              <tr>
                <td className="py-2" colSpan="2">
                  <strong style={{color:'DarkSlateBlue'}}>High Risk Cookies:</strong>
                  {scanData.cookies_high_risk_cookies?.length > 0 ? (
                    <div className="space-y-2 bg-red-50 rounded border border-red-200">
                      {scanData.cookies_high_risk_cookies.map((cookie, index) => ( 
                          <div>
                            <span className="font-semibold">Name: </span><span style={{ backgroundColor:"orange"}}>{cookie.name}</span>
                         
                            <span className="font-semibold">&nbsp; Issues:</span>
                            <span>
                              {cookie.issues?.map((issue, i) => (
                                <span style={{ backgroundColor:"orange"}} key={i}>{issue}</span>
                              ))}
                            </span>
                            <span className="font-semibold">&nbsp; Expiration:</span> <span style={{ backgroundColor:"orange"}}>{
                              cookie.expiration_days === null || cookie.expiration_days === undefined 
                                ? 'None' 
                                : `${cookie.expiration_days} days`
                            }</span>
                          </div>   
                      ))}
                    </div>
                  ) : (
                    <span className="text-sm text-gray-500">No high-risk cookies found</span>
                  )}
                </td>
              </tr>
              <tr>
                <td colSpan="2"><strong>Cookies in play:</strong></td>
              </tr>
              <tr>
                <td className="py-2" colSpan="2">
                  {scanData.data_analysis?.cookies?.length > 0 ? (
                    <div 
                          id="dvCookies" 
                          ref={cookiesContainerRef}
                          className="font-mono text-sm bg-black p-2 rounded overflow-y-scroll max-h-60 w-full text-green-400 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-900"
                        >
                      {scanData.data_analysis.cookies.map((cookie, index) => (
                        <div 
                          key={index} 
                          className="mb-3 break-all whitespace-pre-wrap overflow-hidden"
                          style={{ wordBreak: 'break-word' }}
                        >
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2">
                            <div><span className="font-semibold text-green-300">Domain:</span> <span className="text-green-400">{cookie.domain}</span></div>
                            <div><span className="font-semibold text-green-300">Name:</span> <span className="text-green-400">{cookie.name}</span></div>
                            <div><span className="font-semibold text-green-300">Value:</span> <span className="break-all text-green-400">{cookie.value}</span></div>
                            <div><span className="font-semibold text-green-300">Expiry:</span> <span className="text-green-400">{cookie.expiry || 'None'}</span></div>
                            <div><span className="font-semibold text-green-300">Path:</span> <span className="text-green-400">{cookie.path}</span></div>
                            <div><span className="font-semibold text-green-300">Secure:</span> <span className="text-green-400">{cookie.secure ? 'Yes' : 'No'}</span></div>
                            <div><span className="font-semibold text-green-300">HttpOnly:</span> <span className="text-green-400">{cookie.httpOnly ? 'Yes' : 'No'}</span></div>
                            <div><span className="font-semibold text-green-300">SameSite:</span> <span className="text-green-400">{cookie.sameSite || 'None'}</span></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span className="text-sm text-gray-500">No cookies found</span>
                  )}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        {/* BOTS */}
        <div className="bg-white p-4 rounded-lg shadow md:col-span-2 lg:col-span-2">
          <table className="w-full" style={{ padding: '5px' }}>
            <tbody>
              <tr>
                <td style={{ backgroundColor: 'DarkSlateBlue', color: 'white', borderRadius: '7.5px' }} 
                    colSpan="3" 
                    className="font-bold text-lg p-2" >
                    LOCAL STORAGE
                  </td>
              </tr>
             <tr>
                <td className="py-2" colSpan="3">
                  {Object.keys(scanData.data_analysis?.local_storage || {}).length > 0 ? (
                    <div 
                        id="dvLocalStorage" 
                        ref={localStorageContainerRef}
                        className="font-mono text-sm bg-black p-2 rounded text-green-400"
                        style={{
                          width: '100%',
                          height: '490px',
                          overflowY: 'auto',
                          display: 'flex',
                          flexDirection: 'column'
                        }}
                      >
                      {Object.entries(scanData.data_analysis.local_storage).map(([key, value], index) => (
                        <div 
                          key={index} 
                          className="mb-3 break-all whitespace-pre-wrap"
                          style={{ 
                            wordBreak: 'break-word',
                            width: '100%',
                            padding: '8px',
                            borderBottom: '1px solid #2d3748' // subtle separator
                          }}
                        >
                          <div className="flex flex-col">
                            <div><span className="font-semibold text-green-300">Key:</span> <span className="text-green-400">{key}</span></div>
                            <div className="mt-1">
                              <span className="font-semibold text-green-300">Value:</span> 
                              <div className="text-green-400 overflow-auto max-h-40" style={{ wordBreak: 'break-word' }}>
                                {value}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span className="text-sm text-gray-500">No local storage data found</span>
                  )}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        {/* DATA EXFILTRATION */}
        {/* <div className="bg-white p-4 rounded-lg shadow">
          <table className="w-full" style={{ padding: '5px' }}>
            <tbody>
              <tr>
                <td style={{ backgroundColor: 'DarkSlateBlue', color: 'white', borderRadius: '7.5px' }} 
                    colSpan="3" 
                    className="font-bold text-lg p-2" >
                    Data Exfiltration
                  </td>
              </tr>
              <tr>
                <td className="py-2"><strong style={{color:'DarkSlateBlue'}}>Risk Count:</strong></td>
                <td className="py-2"><span className="text-lg text-red-600 "><strong>0</strong></span></td>
              </tr>
              <tr> 
                <td className="py-2 align-top"><strong style={{color:'DarkSlateBlue'}}>Risk Items:</strong></td>
                <td className="py-2"  colSpan="2" >
                  No data exfiltration detected
                </td>
              </tr>
            </tbody>
          </table>
        </div> */}

        {/* LOCAL CACHE */}
        {/* <div className="bg-white p-3 rounded-lg shadow">
          <table className="w-full" style={{ padding: '5px' }}>
            <tbody>
              <tr>
                <td style={{ backgroundColor: 'DarkSlateBlue', color: 'white', borderRadius: '7.5px' }} 
                    colSpan="3" 
                    className="font-bold text-lg p-2" >
                    Local Cache
                  </td>
              </tr>
              <tr>
                <td className="py-2"><strong style={{color:'DarkSlateBlue'}}>Risk Count:</strong></td>
                <td className="py-2"><span className="text-lg text-red-600 "><strong>0</strong></span></td>
              </tr>
              <tr> 
                <td className="py-2 align-top"><strong style={{color:'DarkSlateBlue'}}>Risk Items:</strong></td>
                <td className="py-2"  colSpan="2" >
                  No sensitive data found in local cache
                </td>
              </tr>
            </tbody>
          </table>
        </div> */}
      </div>
    </div>
  );
};

export default SecurityAnalysisApp;
