# Requirements Document

## Introduction

Bu özellik, mevcut chatbot altyapısına "Öğretmen-Öğrenci" ve "AI Denetçi" mimarilerini entegre ederek, sistemin kendi yaptığı hataları (özellikle "sessiz hataları") otomatik olarak tespit etmesini ve bu hatalardan öğrenerek kendini geliştirmesini sağlar. Sistem, canlı trafikte hızlı Gemini 1.5 Flash modeli kullanırken, arka planda güçlü Gemini 1.5 Pro modelleri ile kalite kontrolü ve eğitim verisi üretimi yapar.

## Requirements

### Requirement 1

**User Story:** Sistem yöneticisi olarak, chatbot'un yaptığı hataları otomatik olarak tespit etmesini istiyorum, böylece manuel kalite kontrolü yapmak zorunda kalmam.

#### Acceptance Criteria

1. WHEN sistem saatlik periyodik denetleme çalıştırıldığında THEN son 1 saatteki tüm konuşma logları Denetçi Model tarafından analiz edilmeli
2. WHEN Denetçi Model bir log çiftini (input_text, output_json) incelediğinde THEN botun yanıtının doğru/hatalı olduğunu %80+ güvenle tespit etmeli
3. WHEN hatalı bir yanıt tespit edildiğinde THEN hata türü (intent_error, entity_error, confidence_error, response_error) kategorize edilmeli
4. WHEN hatalı loglar tespit edildiğinde THEN bu loglar insan onayı için ayrı bir tabloya/dosyaya kaydedilmeli
5. IF sistem 1000+ log biriktirirse THEN otomatik denetleme tetiklenmeli

### Requirement 2

**User Story:** Kalite kontrol uzmanı olarak, AI Denetçi'nin bulduğu hataları gözden geçirip onaylayabilmek istiyorum, böylece yanlış eğitim verilerinin sisteme girmesini engelleyebilirim.

#### Acceptance Criteria

1. WHEN hatalı loglar tespit edildiğinde THEN bu loglar "pending_review" statüsü ile kaydedilmeli
2. WHEN insan onayı bekleyen loglar listelendiğinde THEN hata açıklaması, orijinal input/output ve önerilen düzeltme gösterilmeli
3. WHEN bir hata logu onaylandığında THEN status "approved" olarak güncellenmeli ve eğitim verisi hazırlama sürecine dahil edilmeli
4. WHEN bir hata logu reddedildiğinde THEN status "rejected" olarak güncellenmeli ve eğitim verisi üretilmemeli
5. IF insan düzeltme yaparsa THEN düzeltilmiş veri kaydedilmeli ve eğitim için kullanılmalı

### Requirement 3

**User Story:** Sistem yöneticisi olarak, onaylanmış hatalardan otomatik olarak yeni eğitim verileri üretilmesini istiyorum, böylece fine-tuning için kaliteli veri setim sürekli büyüsün.

#### Acceptance Criteria

1. WHEN onaylanmış hata logları bulunduğunda THEN Öğretmen Model bu hatalardan yeni eğitim örnekleri üretmeli
2. WHEN Öğretmen Model eğitim verisi ürettiğinde THEN orijinal örnek + 3 varyasyon oluşturmalı
3. WHEN eğitim verileri üretildiğinde THEN JSONL formatında fine-tuning için hazır hale getirilmeli
4. WHEN yeni eğitim verileri hazırlandığında THEN bu veriler insan onayı için "pending_review" statüsünde kaydedilmeli
5. IF günlük eğitim verisi hazırlama zamanı geldiğinde THEN sistem otomatik olarak yeni eğitim örnekleri üretmeli

### Requirement 4

**User Story:** Sistem yöneticisi olarak, Learning Service'in performansını ve istatistiklerini takip edebilmek istiyorum, böylece sistemin ne kadar etkili çalıştığını görebilirim.

#### Acceptance Criteria

1. WHEN denetleme işlemi tamamlandığında THEN toplam log sayısı, tespit edilen hata sayısı ve hata kategorileri kaydedilmeli
2. WHEN istatistikler sorgulandığında THEN son denetleme zamanı, toplam denetlenen log sayısı ve hata oranları gösterilmeli
3. WHEN eğitim verisi üretildiğinde THEN üretilen örnek sayısı ve kaynak hata sayısı istatistiklere eklenmeli
4. WHEN sistem durumu sorgulandığında THEN scheduler durumu, son çalışma zamanları ve hata logları gösterilmeli
5. IF hata oranı %10'u geçerse THEN sistem yöneticisine uyarı gönderilmeli

### Requirement 5

**User Story:** Geliştirici olarak, Learning Service'i manuel olarak tetikleyebilmek istiyorum, böylece test amaçlı veya acil durumlarda sistemi çalıştırabilirim.

#### Acceptance Criteria

1. WHEN manuel denetleme tetiklendiğinde THEN belirtilen log sayısı veya session ID'si için denetleme yapılmalı
2. WHEN manuel eğitim verisi üretimi tetiklendiğinde THEN bekleyen tüm onaylanmış hatalar işlenmeli
3. WHEN fine-tuning veri seti oluşturma tetiklendiğinde THEN tüm onaylanmış eğitim verileri JSONL formatında export edilmeli
4. WHEN Learning Service konfigürasyonu güncellendiğinde THEN yeni ayarlar scheduler'a uygulanmalı
5. IF sistem durdurulup başlatıldığında THEN tüm scheduler görevleri otomatik olarak yeniden başlamalı

### Requirement 6

**User Story:** Sistem yöneticisi olarak, farklı hata türleri için farklı işlem stratejileri uygulayabilmek istiyorum, böylece kritik hataları daha hızlı düzeltebilirim.

#### Acceptance Criteria

1. WHEN intent hatası tespit edildiğinde THEN bu hata "high" öncelik ile işaretlenmeli
2. WHEN entity hatası tespit edildiğinde THEN eksik/yanlış entity'ler detaylandırılmalı
3. WHEN confidence hatası tespit edildiğinde THEN gerçek confidence skoru ile karşılaştırma yapılmalı
4. WHEN response hatası tespit edildiğinde THEN kullanıcı sorusuna uygunluk analizi yapılmalı
5. IF kritik hata türleri tespit edilirse THEN bu hatalar öncelikli olarak işlenmeli

### Requirement 7

**User Story:** Sistem yöneticisi olarak, Learning Service'in güvenli bir şekilde çalışmasını istiyorum, böylece mevcut sistemi bozmadan iyileştirmeler yapabileyim.

#### Acceptance Criteria

1. WHEN Learning Service başlatıldığında THEN mevcut sistemin performansını etkilememeli
2. WHEN denetleme işlemi çalıştığında THEN canlı trafik kesintiye uğramamalı
3. WHEN hata tespit edildiğinde THEN orijinal loglar değiştirilmemeli, sadece kopyaları işlenmeli
4. WHEN eğitim verileri üretildiğinde THEN insan onayı olmadan otomatik fine-tuning yapılmamalı
5. IF sistem hatası oluşursa THEN Learning Service durmalı ama ana chatbot çalışmaya devam etmeli