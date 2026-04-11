import React, { useEffect, useState } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'loose',
});

const Mermaid = ({ chart }) => {
  const [svgHtml, setSvgHtml] = useState('<div class="loading-spinner"></div>');

  useEffect(() => {
    if (!chart) return;
    
    const renderChart = async () => {
      try {
        const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;
        const { svg } = await mermaid.render(id, chart);
        setSvgHtml(svg);
      } catch (e) {
        console.error('Mermaid render error:', e);
        setSvgHtml('<p style="color:var(--red);">Syntax error in mindmap layout.</p>');
      }
    };
    renderChart();
  }, [chart]);

  return <div dangerouslySetInnerHTML={{ __html: svgHtml }} />;
};

export default Mermaid;
