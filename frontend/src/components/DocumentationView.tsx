import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { FileText, Download, Copy, Check } from 'lucide-react';
import type { DocumentationOutput } from '../types';
import './DocumentationView.css';

interface DocumentationViewProps {
  documentation: DocumentationOutput;
}

export default function DocumentationView({ documentation }: DocumentationViewProps) {
  const [copied, setCopied] = useState(false);

  const handleDownload = () => {
    const blob = new Blob([documentation.content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `architecture-${Date.now()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(documentation.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Metadata and Actions */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <FileText className="w-6 h-6 text-blue-600" />
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">
              High-Level Design Document
            </h3>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleCopy}
              className="flex items-center space-x-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition"
            >
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              <span>{copied ? 'Copied!' : 'Copy'}</span>
            </button>
            <button
              onClick={handleDownload}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              <Download className="w-4 h-4" />
              <span>Download</span>
            </button>
          </div>
        </div>

        {/* Metadata */}
        {documentation.metadata && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500 dark:text-gray-400">Format:</span>
              <p className="text-gray-900 dark:text-white font-medium">{documentation.format}</p>
            </div>
            {documentation.metadata.cloud_platform && (
              <div>
                <span className="text-gray-500 dark:text-gray-400">Cloud Platform:</span>
                <p className="text-gray-900 dark:text-white font-medium">{documentation.metadata.cloud_platform}</p>
              </div>
            )}
            {documentation.metadata.generated_at && (
              <div>
                <span className="text-gray-500 dark:text-gray-400">Generated:</span>
                <p className="text-gray-900 dark:text-white font-medium">
                  {new Date(documentation.metadata.generated_at).toLocaleString()}
                </p>
              </div>
            )}
            {documentation.metadata.version && (
              <div>
                <span className="text-gray-500 dark:text-gray-400">Version:</span>
                <p className="text-gray-900 dark:text-white font-medium">{documentation.metadata.version}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Markdown Content */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8">
        <div className="documentation-content prose prose-lg dark:prose-invert max-w-none 
                        prose-headings:font-bold prose-headings:text-gray-900 dark:prose-headings:text-white
                        prose-h1:text-3xl prose-h1:mb-6 prose-h1:mt-8 prose-h1:border-b prose-h1:pb-3
                        prose-h2:text-2xl prose-h2:mb-4 prose-h2:mt-6
                        prose-h3:text-xl prose-h3:mb-3 prose-h3:mt-5
                        prose-p:text-gray-700 dark:prose-p:text-gray-300 prose-p:leading-relaxed prose-p:mb-4
                        prose-ul:my-4 prose-ul:space-y-2 prose-li:text-gray-700 dark:prose-li:text-gray-300
                        prose-ol:my-4 prose-ol:space-y-2
                        prose-strong:text-gray-900 dark:prose-strong:text-white prose-strong:font-semibold
                        prose-code:text-blue-600 dark:prose-code:text-blue-400 prose-code:bg-gray-100 dark:prose-code:bg-gray-900 
                        prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm
                        prose-pre:bg-gray-900 dark:prose-pre:bg-black prose-pre:text-gray-100 
                        prose-pre:p-4 prose-pre:rounded-lg prose-pre:overflow-x-auto
                        prose-a:text-blue-600 dark:prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline
                        prose-blockquote:border-l-4 prose-blockquote:border-blue-600 prose-blockquote:pl-4 
                        prose-blockquote:italic prose-blockquote:text-gray-600 dark:prose-blockquote:text-gray-400
                        prose-table:border-collapse prose-table:w-full
                        prose-th:bg-gray-100 dark:prose-th:bg-gray-700 prose-th:p-3 prose-th:text-left
                        prose-td:border prose-td:border-gray-300 dark:prose-td:border-gray-600 prose-td:p-3
                        prose-img:rounded-lg prose-img:shadow-md">
          <ReactMarkdown>{documentation.content}</ReactMarkdown>
        </div>
      </div>

      {/* Diagrams (if any) */}
      {documentation.diagrams && documentation.diagrams.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            Additional Diagrams ({documentation.diagrams.length})
          </h3>
          <div className="space-y-4">
            {documentation.diagrams.map((diagram, index) => (
              <div key={index} className="border dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-gray-900 dark:text-white">{diagram.name}</h4>
                  <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
                    {diagram.format}
                  </span>
                </div>
                <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded overflow-x-auto">
                  <pre className="text-sm text-gray-800 dark:text-gray-200">{diagram.content}</pre>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}



      {/* Export Options */}
      <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 text-sm text-gray-600 dark:text-gray-400">
        <p className="font-medium mb-2">Export Options:</p>
        <ul className="list-disc list-inside space-y-1">
          <li>Download as Markdown (.md) - Click the Download button above</li>
          <li>Copy to clipboard - Click the Copy button above</li>
          <li>Print as PDF - Use your browser's print function (Ctrl/Cmd + P)</li>
        </ul>
      </div>
    </div>
  );
}
