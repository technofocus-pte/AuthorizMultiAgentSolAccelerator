"use client";

import { useState } from "react";
import type { ReviewResponse } from "@/lib/types";
import { Header } from "@/components/header";
import { UploadForm } from "@/components/upload-form";
import { ReviewDashboard } from "@/components/review-dashboard";

export default function Home() {
  const [review, setReview] = useState<ReviewResponse | null>(null);

  return (
    <main className="mx-auto max-w-4xl px-4 py-8 sm:py-12">
      <Header />
      <UploadForm onReviewComplete={setReview} />
      {review && <ReviewDashboard review={review} />}
    </main>
  );
}
