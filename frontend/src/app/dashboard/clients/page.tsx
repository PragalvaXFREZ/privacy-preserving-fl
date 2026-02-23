"use client";

import { useEffect, useState } from "react";
import { getClients, getClientTrust } from "@/lib/api";
import type { Client, TrustScore } from "@/lib/types";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import ClientTable from "@/components/clients/ClientTable";
import TrustScoreChart from "@/components/charts/TrustScoreChart";

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedClientId, setSelectedClientId] = useState<number | null>(null);
  const [trustData, setTrustData] = useState<TrustScore[]>([]);
  const [trustLoading, setTrustLoading] = useState(false);

  useEffect(() => {
    async function fetchClients() {
      try {
        const data = await getClients();
        setClients(data);
      } catch (err) {
        console.error("Failed to fetch clients:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchClients();
  }, []);

  const handleClientClick = async (id: number) => {
    if (selectedClientId === id) {
      setSelectedClientId(null);
      setTrustData([]);
      return;
    }

    setSelectedClientId(id);
    setTrustLoading(true);
    try {
      const data = await getClientTrust(id);
      setTrustData(data);
    } catch (err) {
      console.error("Failed to fetch trust data:", err);
      setTrustData([]);
    } finally {
      setTrustLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-96 animate-pulse rounded-lg bg-gray-200" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Client Nodes</CardTitle>
        </CardHeader>
        <CardContent>
          <ClientTable clients={clients} onClientClick={handleClientClick} />
        </CardContent>
      </Card>

      {selectedClientId !== null && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              Trust Score History -{" "}
              {clients.find((c) => c.id === selectedClientId)?.name || "Client"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {trustLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
                <span className="ml-2 text-sm text-gray-500">
                  Loading trust scores...
                </span>
              </div>
            ) : trustData.length > 0 ? (
              <TrustScoreChart data={trustData} />
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">
                No trust score data available for this client.
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
