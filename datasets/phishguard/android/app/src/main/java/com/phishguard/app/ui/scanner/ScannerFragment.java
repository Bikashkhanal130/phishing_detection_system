package com.phishguard.app.ui.scanner;

import android.graphics.Color;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.content.ContextCompat;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.ViewModelProvider;

import com.phishguard.app.R;
import com.phishguard.app.databinding.FragmentScannerBinding;
import com.phishguard.app.ml.PredictionResult;

/** Scanner tab: enter a URL, run the on-device model, show a coloured result card. */
public class ScannerFragment extends Fragment {

    private FragmentScannerBinding binding;
    private ScannerViewModel viewModel;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        binding = FragmentScannerBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        viewModel = new ViewModelProvider(this).get(ScannerViewModel.class);

        binding.btnScan.setOnClickListener(v -> {
            String url = binding.etUrl.getText() == null ? "" : binding.etUrl.getText().toString();
            viewModel.scan(url);
        });

        viewModel.getLoading().observe(getViewLifecycleOwner(), loading -> {
            binding.progress.setVisibility(Boolean.TRUE.equals(loading) ? View.VISIBLE : View.GONE);
            binding.btnScan.setEnabled(!Boolean.TRUE.equals(loading));
        });

        viewModel.getResult().observe(getViewLifecycleOwner(), this::showResult);

        viewModel.getError().observe(getViewLifecycleOwner(), err -> {
            if (err != null && !err.isEmpty()) {
                android.widget.Toast.makeText(requireContext(), err, android.widget.Toast.LENGTH_LONG).show();
            }
        });
    }

    private void showResult(PredictionResult result) {
        if (result == null) {
            return;
        }
        binding.resultCard.setVisibility(View.VISIBLE);

        if (result.isPhishing()) {
            binding.resultCard.setCardBackgroundColor(
                    ContextCompat.getColor(requireContext(), R.color.phishing_red_bg));
            binding.tvResultBadge.setText(R.string.result_phishing);
            binding.tvResultBadge.setTextColor(
                    ContextCompat.getColor(requireContext(), R.color.phishing_red));
        } else {
            binding.resultCard.setCardBackgroundColor(
                    ContextCompat.getColor(requireContext(), R.color.safe_green_bg));
            binding.tvResultBadge.setText(R.string.result_safe);
            binding.tvResultBadge.setTextColor(
                    ContextCompat.getColor(requireContext(), R.color.safe_green));
        }

        binding.tvConfidence.setText("Confidence: " + result.getConfidencePercent() + "%");
        binding.tvScannedUrl.setText(result.getUrl());
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }
}
