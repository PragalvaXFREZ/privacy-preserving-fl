"use client";

import { useState, useEffect, useCallback } from "react";
import { getTrainingRounds, getCurrentRound } from "@/lib/api";
import type { TrainingRound } from "@/lib/types";

export function useTrainingRounds() {
  const [rounds, setRounds] = useState<TrainingRound[]>([]);
  const [currentRound, setCurrentRound] = useState<TrainingRound | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchRounds = useCallback(async () => {
    try {
      const data = await getTrainingRounds();
      setRounds(data);
    } catch (err) {
      console.error("Failed to fetch training rounds:", err);
    }
  }, []);

  const fetchCurrentRound = useCallback(async () => {
    try {
      const data = await getCurrentRound();
      setCurrentRound(data);
    } catch {
      setCurrentRound(null);
    }
  }, []);

  useEffect(() => {
    async function init() {
      setLoading(true);
      await Promise.all([fetchRounds(), fetchCurrentRound()]);
      setLoading(false);
    }
    init();

    const interval = setInterval(fetchCurrentRound, 10000);
    return () => clearInterval(interval);
  }, [fetchRounds, fetchCurrentRound]);

  return { rounds, currentRound, loading, refetch: fetchRounds };
}
