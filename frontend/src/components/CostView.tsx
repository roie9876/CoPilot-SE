import { DollarSign, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';
import type { CostOutput } from '../types';

interface CostViewProps {
  costs: CostOutput;
}

export default function CostView({ costs }: CostViewProps) {
  // Calculate cost by category
  const costsByCategory = costs.service_costs.reduce((acc, service) => {
    const category = service.category;
    if (!acc[category]) {
      acc[category] = { low: 0, medium: 0, high: 0, count: 0 };
    }
    acc[category].low += service.low_usage_monthly;
    acc[category].medium += service.medium_usage_monthly;
    acc[category].high += service.high_usage_monthly;
    acc[category].count += 1;
    return acc;
  }, {} as Record<string, { low: number; medium: number; high: number; count: number }>);

  return (
    <div className="space-y-6">
      {/* Total Cost Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg shadow p-6 border-2 border-green-200 dark:border-green-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-green-700 dark:text-green-300">LOW Usage</span>
            <TrendingUp className="w-5 h-5 text-green-600" />
          </div>
          <div className="flex items-baseline space-x-1">
            <DollarSign className="w-6 h-6 text-green-600" />
            <span className="text-3xl font-bold text-green-700 dark:text-green-300">
              {costs.total_monthly_cost_low.toFixed(2)}
            </span>
            <span className="text-sm text-green-600">/month</span>
          </div>
        </div>

        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg shadow p-6 border-2 border-blue-200 dark:border-blue-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-blue-700 dark:text-blue-300">MEDIUM Usage</span>
            <TrendingUp className="w-5 h-5 text-blue-600" />
          </div>
          <div className="flex items-baseline space-x-1">
            <DollarSign className="w-6 h-6 text-blue-600" />
            <span className="text-3xl font-bold text-blue-700 dark:text-blue-300">
              {costs.total_monthly_cost_medium.toFixed(2)}
            </span>
            <span className="text-sm text-blue-600">/month</span>
          </div>
        </div>

        <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg shadow p-6 border-2 border-orange-200 dark:border-orange-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-orange-700 dark:text-orange-300">HIGH Usage</span>
            <TrendingUp className="w-5 h-5 text-orange-600" />
          </div>
          <div className="flex items-baseline space-x-1">
            <DollarSign className="w-6 h-6 text-orange-600" />
            <span className="text-3xl font-bold text-orange-700 dark:text-orange-300">
              {costs.total_monthly_cost_high.toFixed(2)}
            </span>
            <span className="text-sm text-orange-600">/month</span>
          </div>
        </div>
      </div>

      {/* Service Cost Breakdown */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center space-x-2">
          <DollarSign className="w-6 h-6 text-blue-600" />
          <span>Service Cost Breakdown ({costs.service_costs.length} services)</span>
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b dark:border-gray-700">
                <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Service</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Pricing Model</th>
                <th className="text-right py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">LOW</th>
                <th className="text-right py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">MEDIUM</th>
                <th className="text-right py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">HIGH</th>
              </tr>
            </thead>
            <tbody>
              {costs.service_costs.map((service, index) => (
                <tr key={index} className="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <td className="py-3 px-4">
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">{service.service_name}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">{service.category}</div>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded">
                      {service.pricing_model}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right text-green-600 dark:text-green-400 font-medium">
                    ${service.low_usage_monthly.toFixed(2)}
                  </td>
                  <td className="py-3 px-4 text-right text-blue-600 dark:text-blue-400 font-medium">
                    ${service.medium_usage_monthly.toFixed(2)}
                  </td>
                  <td className="py-3 px-4 text-right text-orange-600 dark:text-orange-400 font-medium">
                    ${service.high_usage_monthly.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t-2 dark:border-gray-600 font-bold">
                <td colSpan={2} className="py-3 px-4 text-gray-900 dark:text-white">TOTAL</td>
                <td className="py-3 px-4 text-right text-green-600 dark:text-green-400">
                  ${costs.total_monthly_cost_low.toFixed(2)}
                </td>
                <td className="py-3 px-4 text-right text-blue-600 dark:text-blue-400">
                  ${costs.total_monthly_cost_medium.toFixed(2)}
                </td>
                <td className="py-3 px-4 text-right text-orange-600 dark:text-orange-400">
                  ${costs.total_monthly_cost_high.toFixed(2)}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Cost by Category */}
      {Object.keys(costsByCategory).length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            Cost by Category
          </h3>
          <div className="space-y-3">
            {Object.entries(costsByCategory).map(([category, costs]) => (
              <div key={category} className="border dark:border-gray-700 rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium text-gray-900 dark:text-white">{category}</span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">{costs.count} service{costs.count > 1 ? 's' : ''}</span>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">LOW:</span>
                    <span className="ml-2 font-medium text-green-600">${costs.low.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">MED:</span>
                    <span className="ml-2 font-medium text-blue-600">${costs.medium.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">HIGH:</span>
                    <span className="ml-2 font-medium text-orange-600">${costs.high.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cost Optimization Recommendations */}
      {costs.cost_optimization_recommendations.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center space-x-2 mb-4">
            <CheckCircle className="w-6 h-6 text-green-600" />
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">
              Cost Optimization Recommendations
            </h3>
          </div>
          <div className="space-y-3">
            {costs.cost_optimization_recommendations.map((rec, index) => (
              <div key={index} className="flex items-start space-x-3 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-gray-900 dark:text-white font-medium">{rec.recommendation}</p>
                  {rec.estimated_savings_monthly && rec.estimated_savings_monthly > 0 && (
                    <p className="text-sm text-green-600 dark:text-green-400 mt-1">
                      Potential savings: <span className="font-bold">${rec.estimated_savings_monthly.toFixed(2)}/month</span>
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cost Assumptions and Disclaimers */}
      <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg shadow p-6 border border-yellow-200 dark:border-yellow-800">
        <div className="flex items-center space-x-2 mb-3">
          <AlertTriangle className="w-5 h-5 text-yellow-600" />
          <h4 className="font-bold text-gray-900 dark:text-white">Cost Assumptions</h4>
        </div>
        <ul className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
          {costs.assumptions.slice(0, 5).map((assumption, index) => (
            <li key={index} className="flex items-start space-x-2">
              <span className="text-yellow-600">•</span>
              <span>{assumption}</span>
            </li>
          ))}
        </ul>
        <p className="mt-4 text-xs text-gray-600 dark:text-gray-400 border-t border-yellow-200 dark:border-yellow-800 pt-3">
          <strong>Disclaimer:</strong> Cost estimates are approximate (±30% accuracy) and based on publicly available pricing information. 
          Actual costs may vary based on usage patterns, reserved capacity, enterprise discounts, and regional pricing differences. 
          Always use official cloud provider pricing calculators for production planning.
        </p>
      </div>

      {/* Citations */}
      {costs.citations.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h4 className="font-bold text-gray-900 dark:text-white mb-3">Pricing References</h4>
          <ul className="space-y-2 text-sm">
            {costs.citations.map((citation, index) => (
              <li key={index}>
                <a 
                  href={citation.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  {citation.title}
                </a>
                {citation.accessed_at && (
                  <span className="text-gray-500 dark:text-gray-400 ml-2">
                    (Accessed: {new Date(citation.accessed_at).toLocaleDateString()})
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
