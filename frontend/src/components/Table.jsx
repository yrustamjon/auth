import { Loader2, ServerCrash, Inbox } from 'lucide-react';

function Table({ columns, data, loading, error, actions }) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3">
        <Loader2 size={32} className="text-indigo-500 animate-spin" />
        <p className="text-sm text-slate-500">Loading data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3">
        <ServerCrash size={36} className="text-red-400" />
        <p className="text-sm text-red-400 font-medium">Failed to load data</p>
        <p className="text-xs text-slate-600">{error}</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3">
        <Inbox size={36} className="text-slate-600" />
        <p className="text-sm text-slate-500 font-medium">No records found</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
            {columns.map((col) => (
              <th
                key={col.key}
                className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500"
              >
                {col.label}
              </th>
            ))}
            {actions && (
              <th className="text-right px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                Actions
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={row.id ?? i} className="table-row">
              {columns.map((col) => (
                <td key={col.key} className="px-4 py-3.5 text-sm">
                  {col.render ? col.render(row[col.key], row) : (
                    <span className="text-slate-300">
                      {row[col.key] ?? <span className="text-slate-600">—</span>}
                    </span>
                  )}
                </td>
              ))}
              {actions && (
                <td className="px-4 py-3.5 text-right">
                  <div className="flex items-center justify-end gap-2">
                    {actions(row)}
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Table;
