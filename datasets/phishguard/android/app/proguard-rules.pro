# Keep Gson model classes (used reflectively).
-keep class com.phishguard.app.data.model.** { *; }
-keepattributes Signature
-keepattributes *Annotation*

# Retrofit
-dontwarn retrofit2.**
-keep class retrofit2.** { *; }

# ONNX Runtime
-keep class ai.onnxruntime.** { *; }
-dontwarn ai.onnxruntime.**

# iText
-keep class com.itextpdf.** { *; }
-dontwarn com.itextpdf.**
