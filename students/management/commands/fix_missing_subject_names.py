from django.core.management.base import BaseCommand
from students.models import CompartExamRecord, CompartExamConfig


class Command(BaseCommand):
    help = 'Fix missing subject names in CompartExamRecord by matching with CompartExamConfig'

    def handle(self, *args, **options):
        # Find all records with missing subject_name
        null_records = CompartExamRecord.objects.filter(
            subject_name__isnull=True
        ) | CompartExamRecord.objects.filter(subject_name='')
        
        count = 0
        
        for record in null_records:
            try:
                # Try to get subject name from CompartExamConfig
                config = CompartExamConfig.objects.get(subject_code=record.subject_code)
                if config.subject_name:
                    record.subject_name = config.subject_name
                    record.save()
                    count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Updated {record.student.name} - {record.subject_code} -> {config.subject_name}'
                        )
                    )
            except CompartExamConfig.DoesNotExist:
                # If config doesn't exist, use subject_code as name
                record.subject_name = record.subject_code
                record.save()
                count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'Updated {record.student.name} - {record.subject_code} (no config found, used code as name)'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error updating record {record.id}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully updated {count} records with missing subject names')
        )
