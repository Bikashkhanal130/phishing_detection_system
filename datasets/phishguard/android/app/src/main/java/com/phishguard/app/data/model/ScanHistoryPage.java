package com.phishguard.app.data.model;

import java.util.List;

/** Paginated history response: { page, limit, total, items }. */
public class ScanHistoryPage {
    private int page;
    private int limit;
    private int total;
    private List<ScanHistory> items;

    public int getPage() { return page; }
    public void setPage(int page) { this.page = page; }

    public int getLimit() { return limit; }
    public void setLimit(int limit) { this.limit = limit; }

    public int getTotal() { return total; }
    public void setTotal(int total) { this.total = total; }

    public List<ScanHistory> getItems() { return items; }
    public void setItems(List<ScanHistory> items) { this.items = items; }
}
