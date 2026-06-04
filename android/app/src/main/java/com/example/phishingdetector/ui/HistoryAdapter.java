package com.example.phishingdetector.ui;

import android.graphics.Color;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.example.phishingdetector.R;
import com.example.phishingdetector.api.Models;

import java.util.List;

public class HistoryAdapter extends RecyclerView.Adapter<HistoryAdapter.VH> {

    private final List<Models.HistoryItem> items;

    public HistoryAdapter(List<Models.HistoryItem> items) { this.items = items; }

    @NonNull
    @Override
    public VH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View v = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_history, parent, false);
        return new VH(v);
    }

    @Override
    public void onBindViewHolder(@NonNull VH h, int pos) {
        Models.HistoryItem it = items.get(pos);
        h.url.setText(it.url);
        boolean phishing = "Phishing".equalsIgnoreCase(it.result);
        h.result.setText(it.result + "  •  " + String.format("%.1f", it.confidence) + "%");
        h.result.setTextColor(phishing ? Color.parseColor("#C0392B") : Color.parseColor("#1E8E3E"));
        h.date.setText(it.createdAt != null ? it.createdAt.replace("T", " ").substring(0, 16) : "");
    }

    @Override
    public int getItemCount() { return items.size(); }

    static class VH extends RecyclerView.ViewHolder {
        TextView url, result, date;
        VH(@NonNull View v) {
            super(v);
            url = v.findViewById(R.id.tvUrl);
            result = v.findViewById(R.id.tvResult);
            date = v.findViewById(R.id.tvDate);
        }
    }
}
