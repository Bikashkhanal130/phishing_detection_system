package com.example.phishingdetector.ui;

import android.graphics.Color;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
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

        if (phishing) {
            h.result.setText("Phishing");
            h.result.setTextColor(Color.parseColor("#C0392B"));
            h.result.setBackgroundResource(R.drawable.bg_badge_danger);
            h.icon.setImageResource(R.drawable.ic_warning_circle);
        } else {
            h.result.setText("Safe");
            h.result.setTextColor(Color.parseColor("#1E8E3E"));
            h.result.setBackgroundResource(R.drawable.bg_badge_safe);
            h.icon.setImageResource(R.drawable.ic_check_circle);
        }

        String dateStr = it.createdAt != null ? it.createdAt.replace("T", "  ") : "";
        if (dateStr.length() > 16) dateStr = dateStr.substring(0, 16);
        h.date.setText(dateStr);
    }

    @Override
    public int getItemCount() { return items.size(); }

    static class VH extends RecyclerView.ViewHolder {
        TextView url, result, date;
        ImageView icon;
        VH(@NonNull View v) {
            super(v);
            url = v.findViewById(R.id.tvUrl);
            result = v.findViewById(R.id.tvResult);
            date = v.findViewById(R.id.tvDate);
            icon = v.findViewById(R.id.imgResultIcon);
        }
    }
}
