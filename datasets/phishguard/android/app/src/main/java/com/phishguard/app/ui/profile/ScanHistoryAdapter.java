package com.phishguard.app.ui.profile;

import android.graphics.drawable.GradientDrawable;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.RecyclerView;

import com.phishguard.app.R;
import com.phishguard.app.data.model.ScanHistory;

import java.util.ArrayList;
import java.util.List;

/** RecyclerView adapter for the scan history list. */
public class ScanHistoryAdapter extends RecyclerView.Adapter<ScanHistoryAdapter.VH> {

    private final List<ScanHistory> items = new ArrayList<>();

    public void setItems(List<ScanHistory> newItems) {
        items.clear();
        if (newItems != null) {
            items.addAll(newItems);
        }
        notifyDataSetChanged();
    }

    public ScanHistory getItem(int position) {
        return items.get(position);
    }

    public void removeAt(int position) {
        items.remove(position);
        notifyItemRemoved(position);
    }

    @NonNull
    @Override
    public VH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View v = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_scan_history, parent, false);
        return new VH(v);
    }

    @Override
    public void onBindViewHolder(@NonNull VH holder, int position) {
        ScanHistory item = items.get(position);
        holder.tvUrl.setText(item.getUrl());
        holder.tvDate.setText(formatDate(item.getScannedAt()));

        int pct = Math.round(item.getConfidence() * 100f);
        holder.tvConfidence.setText(pct + "%");

        GradientDrawable bg = new GradientDrawable();
        bg.setCornerRadius(dp(holder.itemView, 12));
        if (item.isPhishing()) {
            holder.tvBadge.setText(R.string.result_phishing);
            bg.setColor(ContextCompat.getColor(holder.itemView.getContext(), R.color.phishing_red));
        } else {
            holder.tvBadge.setText(R.string.result_safe);
            bg.setColor(ContextCompat.getColor(holder.itemView.getContext(), R.color.safe_green));
        }
        holder.tvBadge.setBackground(bg);
    }

    @Override
    public int getItemCount() {
        return items.size();
    }

    private static float dp(View v, int value) {
        return value * v.getResources().getDisplayMetrics().density;
    }

    /** Backend sends ISO-ish timestamps; show the date+time portion cleanly. */
    private static String formatDate(String raw) {
        if (raw == null) {
            return "";
        }
        String s = raw.replace("T", " ");
        int dot = s.indexOf('.');
        if (dot != -1) {
            s = s.substring(0, dot);
        }
        // Trim timezone offset if present.
        int plus = s.indexOf('+');
        if (plus != -1) {
            s = s.substring(0, plus).trim();
        }
        return s.length() > 16 ? s.substring(0, 16) : s;
    }

    static class VH extends RecyclerView.ViewHolder {
        final android.widget.TextView tvUrl;
        final android.widget.TextView tvDate;
        final android.widget.TextView tvBadge;
        final android.widget.TextView tvConfidence;

        VH(@NonNull View itemView) {
            super(itemView);
            tvUrl = itemView.findViewById(R.id.tvUrl);
            tvDate = itemView.findViewById(R.id.tvDate);
            tvBadge = itemView.findViewById(R.id.tvBadge);
            tvConfidence = itemView.findViewById(R.id.tvConfidence);
        }
    }
}
