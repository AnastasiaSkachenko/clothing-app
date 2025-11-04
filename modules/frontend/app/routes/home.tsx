import { useState, useEffect } from "react";
import type { Route } from "./+types/home";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "~/components/ui/card";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { Label } from "~/components/ui/label";
import { Badge } from "~/components/ui/badge";
import { Trash2, Plus, ExternalLink, Loader2, Search } from "lucide-react";
import { toast } from "sonner";
import { apiClient, type ImageUrl, type SearchSimilarResponse } from "@/lib/apiClient";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "URL Manager" },
    { name: "description", content: "Manage and store your image URLs" },
  ];
}

export default function Home() {
  const [urls, setUrls] = useState<ImageUrl[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [newUrl, setNewUrl] = useState("");
  const [newTitle, setNewTitle] = useState("");
  const [searchUrl, setSearchUrl] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchSimilarResponse | null>(null);

  // Load URLs on mount
  useEffect(() => {
    loadUrls();
  }, []);

  const loadUrls = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getImages();
      setUrls(data);
    } catch (error) {
      console.error("Failed to load URLs:", error);
      toast.error("Failed to load URLs. Make sure the API is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newUrl.trim()) {
      toast.error("Please enter a URL");
      return;
    }

    try {
      setSubmitting(true);
      const created = await apiClient.createImage({
        url: newUrl,
        title: newTitle || undefined,
        tags: [],
      });
      
      setUrls([created, ...urls]);
      setNewUrl("");
      setNewTitle("");
      toast.success("URL added successfully!");
    } catch (error) {
      console.error("Failed to create URL:", error);
      toast.error(error instanceof Error ? error.message : "Failed to add URL");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiClient.deleteImage(id);
      setUrls(urls.filter((url) => url.id !== id));
      toast.success("URL deleted successfully!");
    } catch (error) {
      console.error("Failed to delete URL:", error);
      toast.error("Failed to delete URL");
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!searchUrl.trim()) {
      toast.error("Please enter an image URL to search");
      return;
    }

    try {
      setSearching(true);
      const results = await apiClient.searchSimilarProducts({
        image_url: searchUrl,
      });
      setSearchResults(results);
      toast.success("Search completed!");
    } catch (error) {
      console.error("Failed to search:", error);
      toast.error(error instanceof Error ? error.message : "Failed to search for similar products");
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-foreground">Visual Search</h1>
          <p className="text-muted-foreground">
            Search for similar clothing products using image URLs
          </p>
        </div>

        {/* Search Form */}
        <Card>
          <CardHeader>
            <CardTitle>Search Similar Products</CardTitle>
            <CardDescription>
              Enter an image URL to find visually similar clothing items
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSearch} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="searchUrl">Image URL *</Label>
                <Input
                  id="searchUrl"
                  type="url"
                  placeholder="https://example.com/clothing-image.jpg"
                  value={searchUrl}
                  onChange={(e) => setSearchUrl(e.target.value)}
                  required
                />
              </div>
              <Button type="submit" disabled={searching} className="w-full">
                {searching ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="mr-2 h-4 w-4" />
                    Search Similar Products
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Search Results */}
        {searchResults && (
          <Card>
            <CardHeader>
              <CardTitle>Search Results</CardTitle>
              <CardDescription>
                Found {searchResults.data.result_groups.length} result group(s)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Query Image */}
                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-muted-foreground">Query Image</h3>
                  <img 
                    src={searchResults.data.query_image} 
                    alt="Query" 
                    className="w-full max-w-md mx-auto rounded-lg border"
                  />
                </div>

                {/* Result Groups */}
                {searchResults.data.result_groups.map((group, groupIndex) => (
                  <div key={groupIndex} className="space-y-4">
                    <div className="border-t pt-4">
                      <div className="flex items-center gap-2 mb-3">
                        <h3 className="text-lg font-semibold">
                          Detected: {group.detected_item.name}
                        </h3>
                        <Badge variant="secondary">
                          {(group.detected_item.detection_confidence * 100).toFixed(1)}% confidence
                        </Badge>
                      </div>
                      
                      {/* Detected Item Image */}
                      <img 
                        src={group.detected_item.item_image} 
                        alt={group.detected_item.name}
                        className="w-48 h-48 object-cover rounded-lg border mb-4"
                      />

                      {/* Similar Products */}
                      <div className="space-y-2">
                        <h4 className="text-sm font-medium text-muted-foreground">
                          Similar Products ({group.similar_products.length})
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {group.similar_products.slice(0, 6).map((product) => (
                            <div 
                              key={product.id}
                              className="border rounded-lg overflow-hidden hover:shadow-lg transition-shadow"
                            >
                              <img 
                                src={product.images[0]} 
                                alt={product.name}
                                className="w-full h-48 object-cover"
                              />
                              <div className="p-3 space-y-2">
                                <h5 className="font-medium text-sm line-clamp-2">
                                  {product.name}
                                </h5>
                                <div className="flex items-center justify-between text-xs">
                                  <span className="text-muted-foreground">
                                    {product.brand_name || 'Unknown Brand'}
                                  </span>
                                  <Badge variant="outline">
                                    {(product.score * 100).toFixed(0)}% match
                                  </Badge>
                                </div>
                                <div className="flex items-center justify-between">
                                  <span className="font-semibold text-primary">
                                    {product.currency} {product.price}
                                  </span>
                                  {product.url && (
                                    <a
                                      href={product.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-xs text-primary hover:underline flex items-center gap-1"
                                    >
                                      View
                                      <ExternalLink className="h-3 w-3" />
                                    </a>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Add URL Form */}
        <Card>
          <CardHeader>
            <CardTitle>Add New URL</CardTitle>
            <CardDescription>
              Enter the image URL and an optional title
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="url">Image URL *</Label>
                <Input
                  id="url"
                  type="url"
                  placeholder="https://example.com/image.jpg"
                  value={newUrl}
                  onChange={(e) => setNewUrl(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="title">Title (optional)</Label>
                <Input
                  id="title"
                  type="text"
                  placeholder="My awesome image"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                />
              </div>
              <Button type="submit" disabled={submitting} className="w-full">
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Adding...
                  </>
                ) : (
                  <>
                    <Plus className="mr-2 h-4 w-4" />
                    Add URL
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* URLs List */}
        <Card>
          <CardHeader>
            <CardTitle>Stored URLs</CardTitle>
            <CardDescription>
              {urls.length === 0
                ? "No URLs stored yet"
                : `${urls.length} URL${urls.length === 1 ? "" : "s"} stored`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : urls.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <p>No URLs yet. Add your first one above!</p>
              </div>
            ) : (
              <div className="space-y-3">
                {urls.map((url) => (
                  <div
                    key={url.id}
                    className="flex items-start gap-3 p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex-1 min-w-0 space-y-1">
                      {url.title && (
                        <h3 className="font-medium text-foreground truncate">
                          {url.title}
                        </h3>
                      )}
                      <a
                        href={url.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-primary hover:underline flex items-center gap-1 break-all"
                      >
                        {url.url}
                        <ExternalLink className="h-3 w-3 flex-shrink-0" />
                      </a>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span>
                          Added {new Date(url.created_at).toLocaleDateString()}
                        </span>
                        {url.tags.length > 0 && (
                          <>
                            <span>•</span>
                            <div className="flex gap-1">
                              {url.tags.map((tag) => (
                                <Badge key={tag} variant="secondary">
                                  {tag}
                                </Badge>
                              ))}
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                    <Button
                      variant="destructive"
                      size="icon"
                      onClick={() => handleDelete(url.id)}
                      className="flex-shrink-0"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
