import { useEffect, useState } from 'react';
import { Loader2, ServerCrash, Inbox, SlidersHorizontal, ChevronDown, ChevronLeft, ChevronRight, X } from 'lucide-react';
export default function Table({ columns, data, loading, error, actions, onRowClick, filters = [] }) {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [selectedFilters, setSelectedFilters] = useState({});
  useEffect(() => { setPage(1); }, [data]);
  const rows = (data || []).filter(row => filters.every(filter => {
    const selected = selectedFilters[filter.key];
    return !selected || String(filter.getValue ? filter.getValue(row) : row[filter.key]) === selected;
  }));
  const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const start = (currentPage - 1) * pageSize;
  const visibleRows = rows.slice(start, start + pageSize);
  const pageNumbers = [...new Set([1, currentPage - 1, currentPage, currentPage + 1, totalPages])]
    .filter(number => number >= 1 && number <= totalPages).sort((a, b) => a - b);
  if (loading) return <div className="empty-state" role="status"><Loader2 size={28} className="animate-spin" /><strong>Ma’lumotlar yuklanmoqda...</strong></div>;
  if (error) return <div className="empty-state error" role="alert"><ServerCrash size={30} /><strong>Ma’lumotlarni yuklab bo‘lmadi</strong><p>{error}</p></div>;
  return <>
    {filters.length > 0 && <div className="table-filters">
      <div className="table-filter-heading"><SlidersHorizontal size={16} /><span>Filtrlar</span>{Object.values(selectedFilters).filter(Boolean).length > 0 && <b>{Object.values(selectedFilters).filter(Boolean).length}</b>}</div>
      <div className="table-filter-controls">{filters.map(filter => <label className={`table-filter-select${selectedFilters[filter.key] ? ' is-selected' : ''}`} key={filter.key}><span>{filter.label}</span>
        <select aria-label={`${filter.label} filtri`} value={selectedFilters[filter.key] || ''}
          onChange={event => { setSelectedFilters(values => ({ ...values, [filter.key]: event.target.value })); setPage(1); }}>
          <option value="">Barchasi</option>
          {filter.options.map(option => <option key={String(option.value)} value={String(option.value)}>{option.label}</option>)}
        </select>
        <ChevronDown size={14} aria-hidden="true" />
      </label>)}</div>
      {Object.values(selectedFilters).some(Boolean) && <button type="button" className="table-filter-clear" aria-label="Filtrlarni tozalash" onClick={() => { setSelectedFilters({}); setPage(1); }}><X size={14} />Tozalash</button>}
    </div>}
    {!rows.length ? <div className="empty-state"><Inbox size={30} /><strong>Hozircha ma’lumot yo‘q</strong><p>Yangi yozuv qo‘shing yoki qidiruvni o‘zgartiring.</p></div>
      : <div className="table-scroll" tabIndex={0} aria-label="Ma’lumotlar jadvali"><table className="w-full"><thead><tr>{columns.map(col => <th key={col.key} scope="col" className="text-left px-4 py-3 font-semibold text-slate-500">{col.label}</th>)}{actions && <th scope="col" className="text-right px-4 py-3 text-slate-500">Amallar</th>}</tr></thead><tbody>{visibleRows.map((row,i) => <tr key={row.id ?? start + i} className="table-row" onClick={onRowClick ? ()=>onRowClick(row) : undefined} style={onRowClick ? {cursor:'pointer'} : undefined}>{columns.map(col => <td key={col.key} className="px-4 py-4">{col.render ? col.render(row[col.key],row) : <span className="text-slate-700">{row[col.key] ?? '—'}</span>}</td>)}{actions && <td className="px-4 py-4 text-right"><div className="flex items-center justify-end gap-2">{actions(row)}</div></td>}</tr>)}</tbody></table></div>}
    {rows.length > 0 && <div className="table-pagination">
      <div className="table-pagination-info"><span className="table-result-count" aria-live="polite"><strong>{start + 1}–{Math.min(start + pageSize, rows.length)}</strong><span> / {rows.length} ta yozuv</span></span>
      <label className="table-page-size"><span>Sahifada</span><span className="table-size-select"><select aria-label="Sahifadagi yozuvlar soni" value={pageSize} onChange={event => { setPageSize(Number(event.target.value)); setPage(1); }}>{[10, 25, 50].map(size => <option key={size} value={size}>{size}</option>)}</select><ChevronDown size={13} aria-hidden="true" /></span></label></div>
      <nav aria-label="Jadval sahifalari">
        <button type="button" className="table-page-button table-page-arrow" aria-label="Oldingi" disabled={currentPage === 1} onClick={() => setPage(currentPage - 1)}><ChevronLeft size={16} /></button>
        {pageNumbers.map((number, index) => <span key={number} className="table-page-number">
          {index > 0 && number - pageNumbers[index - 1] > 1 && <span className="table-page-gap" aria-hidden="true">…</span>}
          <button type="button" className={`table-page-button${number === currentPage ? ' is-current' : ''}`} aria-label={`${number}-sahifa`} aria-current={number === currentPage ? 'page' : undefined} onClick={() => setPage(number)}>{number}</button>
        </span>)}
        <span className="table-mobile-page"><strong>{currentPage}</strong> / {totalPages} sahifa</span>
        <button type="button" className="table-page-button table-page-arrow" aria-label="Keyingi" disabled={currentPage === totalPages} onClick={() => setPage(currentPage + 1)}><ChevronRight size={16} /></button>
      </nav>
    </div>}
  </>;
}
